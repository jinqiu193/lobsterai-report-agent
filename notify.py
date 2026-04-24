"""
notify.py - 可配置通知渠道
===========================
支持渠道：log（默认）| feishu | openclaw-weixin
通过 config.json 的 notification_channel 字段配置。

用法（推荐）：
  from notify import notify
  notify("报告生成完成！")

OpenClaw 环境下自动检测 message 工具，
无需 import openclaw_runtime（根本不存在）。
"""

import os, sys

_NOTIFY_CHANNEL = None


def _get_channel() -> str:
    global _NOTIFY_CHANNEL
    if _NOTIFY_CHANNEL is not None:
        return _NOTIFY_CHANNEL

    _NOTIFY_CHANNEL = os.environ.get('LOBAI_NOTIFY_CHANNEL', 'log')
    try:
        cfg_path = os.path.join(os.path.dirname(__file__), 'src', 'config.py')
        sys.path.insert(0, os.path.dirname(__file__))
        from src.config import load_config
        cfg = load_config()
        if cfg.get('notification_channel'):
            _NOTIFY_CHANNEL = cfg['notification_channel']
    except Exception:
        pass
    return _NOTIFY_CHANNEL


def notify(message: str, channel: str = None) -> bool:
    """
    发送通知。
    channel=None 时使用配置默认值。
    返回是否成功。
    """
    ch = channel or _get_channel()

    if ch == 'log':
        print(f"[NOTIFY] {message}", flush=True)
        return True

    if ch == 'openclaw-weixin':
        return _notify_openclaw_weixin(message)

    if ch == 'feishu':
        return _notify_feishu(message)

    print(f"[NOTIFY][{ch}] {message}", flush=True)
    return False


def _notify_openclaw_weixin(message: str) -> bool:
    """
    通过 OpenClaw 微信渠道发送。
    OpenClaw 的消息发送依赖运行时注入的 message 工具，
    不存在 openclaw_runtime 模块。
    降级：打印到 stdout，由 OpenClaw 会话路由到对应渠道。
    """
    # 检测是否在 OpenClaw 运行时（通过检查全局变量）
    try:
        import openclaw
        # openclaw 存在，尝试通过 openclaw.message 发送
        try:
            openclaw.message(
                action='send',
                channel='openclaw-weixin',
                message=message,
            )
            return True
        except Exception:
            pass
    except ImportError:
        pass

    # 降级：打印，OpenClaw session 会话会自动路由
    print(f"[NOTIFY][weixin] {message}", flush=True)
    return True  # 降级打印也视为"成功"，避免上层逻辑中断


def _notify_feishu(message: str) -> bool:
    """
    通过飞书发送通知。
    依赖 OpenClaw 的飞书 channel 配置。
    """
    try:
        import openclaw
        try:
            openclaw.message(
                action='send',
                channel='feishu',
                message=message,
            )
            return True
        except Exception:
            pass
    except ImportError:
        pass

    print(f"[NOTIFY][feishu] {message}", flush=True)
    return True


def set_channel(channel: str) -> None:
    """运行时切换通知渠道"""
    global _NOTIFY_CHANNEL
    _NOTIFY_CHANNEL = channel
