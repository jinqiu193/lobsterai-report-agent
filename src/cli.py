"""
cli.py - CLI 入口
====================
纯 CLI 逻辑，不含业务逻辑。
"""

import sys, glob as glob_module
from . import config
from . import engine


def main():
    argv = sys.argv[1:]
    if '--help' in argv or '-h' in argv:
        print("Usage: python integrate_report.py [command]\n")
        print("Commands:")
        print("  (none)           生成整合报告")
        print("  convert-batch    批量转换 txt -> docx")
        print("  convert-one <in.txt> <out.docx>  单章转换")
        print("  glossary         生成/更新术语表")
        print("  check            跨章一致性审查")
        print("  status           查看撰写进度")
        print("  plan show        查看大纲")
        print("  config show      查看配置")
        print("  ref show|clear  查看/清空参考资料")
        print("  feishu-search <关键词>  搜索飞书知识库（建议在对话中描述需求）")
        print("  doctor           环境健康检查")
        print("\nEnvironment variables:")
        print("  LOBAI_CHAPTERS_DIR    章节目录")
        print("  LOBAI_OUTPUT_DIR      输出目录")
        print("  LOBAI_OUTPUT_FILENAME 输出文件名（默认：整合报告.docx）")
        print("  LOBAI_NOTIFY_CHANNEL  通知渠道：log | feishu | openclaw-weixin")
        return
    if not argv:
        # 默认：生成整合报告
        txt_dir = argv[0] if argv else None
        result = engine.generate_with_accurate_toc(txt_dir=txt_dir)
        if result:
            print(f"\n[DONE] 整合报告生成完成: {result}")
        return

    cmd = argv[0]

    if cmd == '--convert-one':
        if len(argv) != 3:
            print("用法: python integrate_report.py --convert-one <in.txt> <out.docx>")
            sys.exit(1)
        engine.convert_single_chapter_inline(argv[1], argv[2])
        print(f"saved: {argv[2]}", flush=True)

    elif cmd == 'convert-batch':
        txt_dir = argv[1] if len(argv) > 1 else None
        engine.batch_convert_txt_to_docx(txt_dir=txt_dir)

    elif cmd == 'glossary':
        txt_files = sorted(glob_module.glob(config._p('CHAPTERS_DIR') + '/*.txt'))
        ref_text = config.load_reference()
        config.generate_glossary(txt_files, ref_text=ref_text)

    elif cmd == 'check':
        txt_files = sorted(glob_module.glob(config._p('CHAPTERS_DIR') + '/*.txt'))
        chapters_data = engine.parse_chapters(txt_files)
        issues = engine.check_cross_chapter_consistency(chapters_data)
        if not issues:
            print("[OK] 跨章一致性检查通过，无不一致项")
        else:
            for iss in issues:
                print(f"[WARN] {iss}")

    elif cmd == 'status':
        prog = config.load_progress()
        print(f"进度: {prog.get('completed',0)}/{prog.get('total','?')}")
        if prog.get('current'):
            print(f"状态: {prog['current']}")

    elif cmd == 'ref':
        if len(argv) >= 2:
            action = argv[1]
            if action == 'show':
                ref = config.load_reference()
                print(f"参考资料: {len(ref)} 字符")
                print(ref[:500] if ref else "(空)")
            elif action == 'clear':
                config.save_reference("")
                print("参考资料已清空")
        else:
            ref = config.load_reference()
            print(f"当前参考资料: {len(ref)} 字符")

    elif cmd == 'plan':
        # 查看/编辑 plan.json
        if len(argv) >= 2 and argv[1] == 'show':
            import json
            plan = config.load_plan()
            print(json.dumps(plan, ensure_ascii=False, indent=2))

    elif cmd == 'config':
        if len(argv) >= 2 and argv[1] == 'show':
            import json
            cfg = config.load_config()
            print(json.dumps(cfg, ensure_ascii=False, indent=2))

    elif cmd == 'feishu-search':
        # Feishu 搜索是 MCP 工具，不是 CLI 命令
        # OpenClaw Agent 应使用 feishu_search_doc_wiki 工具搜索飞书知识库
        # 本命令仅提示用法
        query = ' '.join(argv[1:]) if len(argv) > 1 else ''
        if not query:
            print("用法: python integrate_report.py feishu-search <关键词>\n")
            print("注意: 这是 MCP 工具命令，请在 OpenClaw 对话中描述搜索需求，")
            print("      Agent 会自动调用 feishu_search_doc_wiki 工具搜索飞书知识库。")
        else:
            print(f"[FEISHU-SEARCH] 关键词: {query}\n")
            print("OpenClaw Agent 请在对话中说：")
            print(f'  "搜索飞书知识库，关键词：{query}"')

    elif cmd == 'doctor':
        engine.doctor()

    else:
        # 未知命令，降级为 generate
        txt_dir = argv[0] if argv else None
        result = engine.generate_with_accurate_toc(txt_dir=txt_dir)
        if result:
            print(f"\n[DONE] 整合报告生成完成: {result}")


if __name__ == '__main__':
    main()
