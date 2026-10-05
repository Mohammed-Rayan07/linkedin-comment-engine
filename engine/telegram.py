"""Telegram delivery via the Bot API, using getUpdates polling (no webhook, no server needed).

Each card has buttons: Posted #1/#2/#3, Skip, New angles. Button taps are picked up on the next run
(or instantly if `python -m engine bot` is running). Never call setWebhook on this bot: it disables getUpdates.
"""
from __future__ import annotations

import html
import logging
from typing import Any, Callable

import httpx

from .config import Config, Lane
from .drafting import Draft
from .models import Post

log = logging.getLogger(__name__)

ANGLE_LABEL = {
    "missing_step": "Missing step",
    "field_detail": "Field detail",
    "pushback": "Pushback",
    "make_concrete": "Make it concrete",
    "sharp_question": "Sharp question",
}
INTENT_LABEL = {"buyer": "🎯 Buyer", "audience": "📣 Audience", "prospect": "⭐ Dream prospect"}


def _ago(hours: float) -> str:
    return f"{int(hours * 60)}m ago" if hours < 1 else f"{hours:.0f}h ago"


def render_card(card_id: int, p: Post, lane: Lane, score: dict[str, Any], prio: float, d: Draft,
                snippet_chars: int = 320) -> str:
    e = html.escape
    snippet = p.text[:snippet_chars] + ("…" if len(p.text) > snippet_chars else "")
    lines = [
        f"<b>#{card_id} · {INTENT_LABEL.get(lane.intent, lane.intent)} · {e(lane.name)} · {prio:.1f}/10</b>",
        f"👤 <b>{e(p.author_name)}</b> · {e(p.author_headline[:110])}",
        f"🕒 {_ago(p.age_hours)} · 👍 {p.likes} · 💬 {p.comments}",
        f"<i>{e(snippet)}</i>",
        f"💡 {e(score.get('why', ''))}",
        f'🔗 <a href="{e(p.url)}">Open post</a>',
        "",
    ]
    for i, o in enumerate(d.options, 1):
        lines.append(f"<b>Option {i} · {ANGLE_LABEL.get(o['angle'], o['angle'])}</b>")
        lines.append(f"<code>{e(o['text'])}</code>")  # tap to copy on mobile
        lines.append("")
    if d.connection_note:
        lines.append("🤝 <b>Connection note</b> (send after your comment):")
        lines.append(f"<code>{e(d.connection_note)}</code>")
    lines.append("")
    lines.append("<i>Edited it? Reply to this message with your final comment so I learn your voice.</i>")
    text = "\n".join(lines)
    # Telegram caps messages at 4096 chars; shrink the snippet rather than cut through an HTML tag
    if len(text) > 4096 and snippet_chars > 0:
        return render_card(card_id, p, lane, score, prio, d, snippet_chars=max(0, snippet_chars - 200))
    return text


def keyboard(card_id: int, n_options: int) -> dict[str, Any]:
    posted = [{"text": f"✅ Posted {i}", "callback_data": f"p:{card_id}:{i}"} for i in range(1, n_options + 1)]
    return {"inline_keyboard": [posted, [
        {"text": "⏭ Skip", "callback_data": f"s:{card_id}"},
        {"text": "🔁 New angles", "callback_data": f"r:{card_id}"},
    ]]}


class Telegram:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.enabled = bool(cfg.s("telegram", "enabled", default=True) and cfg.telegram_token
                            and cfg.telegram_chat_id and not cfg.mock)
        self.base = f"https://api.telegram.org/bot{cfg.telegram_token}"

    def _call(self, method: str, **params: Any) -> Any:
        r = httpx.post(f"{self.base}/{method}", json=params, timeout=60)
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(f"telegram {method} failed: {data.get('description')}")
        return data["result"]

    def send(self, text: str, markup: dict[str, Any] | None = None) -> int | None:
        if not self.enabled:
            print("\n" + "=" * 70 + "\n" + html.unescape(text.replace("<b>", "").replace("</b>", "")
                  .replace("<i>", "").replace("</i>", "").replace("<code>", "").replace("</code>", "")))
            return None
        params: dict[str, Any] = {"chat_id": self.cfg.telegram_chat_id, "text": text, "parse_mode": "HTML",
                                  "disable_web_page_preview": True}
        if markup:
            params["reply_markup"] = markup
        return int(self._call("sendMessage", **params)["message_id"])

    def mark(self, message_id: int, label: str) -> None:
        if not self.enabled or not message_id:
            return
        try:
            self._call("editMessageReplyMarkup", chat_id=self.cfg.telegram_chat_id, message_id=message_id,
                       reply_markup={"inline_keyboard": [[{"text": label, "callback_data": "noop"}]]})
        except RuntimeError as e:
            log.debug("could not update buttons: %s", e)

    def restore(self, message_id: int, card_id: int, n_options: int) -> None:
        """Put the buttons back on a card that was reopened from the dashboard."""
        if not self.enabled or not message_id:
            return
        try:
            self._call("editMessageReplyMarkup", chat_id=self.cfg.telegram_chat_id, message_id=message_id,
                       reply_markup=keyboard(card_id, n_options))
        except RuntimeError as e:
            log.debug("could not restore buttons: %s", e)

    def pin_status(self, store, text: str) -> None:
        """Keep one pinned message at the top of the chat that every run edits in place."""
        if not self.enabled:
            print("\n" + text)
            return
        msg_id = store.get("status_message_id")
        if msg_id:
            try:
                self._call("editMessageText", chat_id=self.cfg.telegram_chat_id, message_id=int(msg_id),
                           text=text, parse_mode="HTML", disable_web_page_preview=True)
                return
            except RuntimeError as e:
                if "not modified" in str(e):
                    return
                log.info("status message gone (%s); posting a new one", e)
        new_id = self.send(text)
        if new_id:
            store.put("status_message_id", str(new_id))
            try:
                self._call("pinChatMessage", chat_id=self.cfg.telegram_chat_id, message_id=new_id,
                           disable_notification=True)
            except RuntimeError as e:
                log.info("could not pin status: %s", e)

    def poll(self, offset: int, timeout: int = 0) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        r = httpx.post(f"{self.base}/getUpdates",
                       json={"offset": offset, "timeout": timeout,
                             "allowed_updates": ["callback_query", "message"]},
                       timeout=timeout + 30)
        return r.json().get("result", [])

    def answer(self, callback_id: str, text: str = "") -> None:
        try:
            self._call("answerCallbackQuery", callback_query_id=callback_id, text=text)
        except RuntimeError:
            pass  # taps older than ~15 min can't be answered; harmless


def process_updates(tg: Telegram, store, handle_action: Callable[[str, int, int | None], str],
                    handle_command: Callable[[str], str], handle_reply: Callable[[int, str], str],
                    timeout: int = 0) -> int:
    """Apply pending button taps / commands. Returns number of updates handled."""
    offset = int(store.get("tg_offset", "0") or 0)
    updates = tg.poll(offset, timeout)
    for u in updates:
        offset = max(offset, u["update_id"] + 1)
        if cq := u.get("callback_query"):
            # only obey the configured chat
            chat_id = str(cq.get("message", {}).get("chat", {}).get("id"))
            if chat_id != str(tg.cfg.telegram_chat_id):
                continue
            parts = (cq.get("data") or "").split(":")
            if parts[0] in ("p", "s", "r") and len(parts) >= 2:
                card_id = int(parts[1])
                opt = int(parts[2]) if len(parts) > 2 else None
                label = handle_action(parts[0], card_id, opt)
                tg.answer(cq["id"], label)
                tg.mark(cq.get("message", {}).get("message_id"), label)
            else:
                tg.answer(cq["id"])
        elif msg := u.get("message"):
            if str(msg.get("chat", {}).get("id")) != str(tg.cfg.telegram_chat_id):
                continue
            text = (msg.get("text") or "").strip()
            replied_to = (msg.get("reply_to_message") or {}).get("message_id")
            reply = handle_reply(replied_to, text) if replied_to else handle_command(text)
            if reply:
                tg.send(reply)
        store.put("tg_offset", str(offset))  # ack as we go so a crash never replays a tap
    return len(updates)
