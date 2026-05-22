import os
import sys
import json
from cryptography.fernet import Fernet

ENCRYPTED_FILE = "targets.enc"
KEY_FILE = "targets.key"


def get_input(prompt, default=None):
    """辅助函数，用于获取用户输入并处理默认值"""
    if default is not None:
        prompt_text = f"{prompt} [{default}]: "
    else:
        prompt_text = f"{prompt}: "

    val = input(prompt_text).strip()
    if not val and default is not None:
        return default
    return val


def print_targets(targets):
    """打印当前的目标列表"""
    if not targets:
        print("\n📝 当前无任何签到目标。")
        return
    print("\n================ 当前配置的签到目标 ================")
    for i, t in enumerate(targets, 1):
        topic_str = f"，话题 ID: {t['topic_id']}" if t.get("topic_id") is not None else ""
        print(
            f"[{i}] 目标: {t['target']} | "
            f"消息: {t['message']} | "
            f"间隔: {t['interval_days']}天{topic_str}"
        )
    print("====================================================")


def add_target(targets):
    """添加一个新目标"""
    print(f"\n--- 正在添加第 {len(targets) + 1} 个目标 ---")

    # 1. Target
    target = get_input("🎯 目标 (必填, 群组ID如-100... / 用户名如@bot)")
    while not target:
        print("❌ 目标不能为空，请重新输入！")
        target = get_input("🎯 目标")

    # 2. Message
    message = get_input("💬 发送的消息 (message)", "/checkin")

    # 3. Interval
    interval_str = get_input("⏰ 间隔天数 (interval_days)", "1")
    try:
        interval_days = int(interval_str)
    except ValueError:
        print("⚠️ 输入无效，默认为 1 天")
        interval_days = 1

    # 4. Topic ID
    topic_id_str = get_input("🧵 话题 ID (topic_id, 若没有则直接回车)", "")

    target_dict = {
        "target": target,
        "message": message,
        "interval_days": interval_days,
    }

    if topic_id_str:
        try:
            target_dict["topic_id"] = int(topic_id_str)
        except ValueError:
            print("⚠️ 话题 ID 必须是数字，已忽略。")

    targets.append(target_dict)
    print("✅ 目标添加成功！")


def edit_target(targets):
    """修改现有目标"""
    print_targets(targets)
    if not targets:
        return

    try:
        idx_str = get_input(f"请输入要修改的目标序号 (1-{len(targets)}) [直接回车返回菜单]")
        if not idx_str:
            return
        idx = int(idx_str) - 1
        if idx < 0 or idx >= len(targets):
            print("❌ 序号超出范围！")
            return
    except ValueError:
        print("❌ 输入无效！")
        return

    t = targets[idx]
    print(f"\n--- 正在修改第 {idx + 1} 个目标 (直接回车保留原值) ---")

    # Target
    target = get_input(f"🎯 目标 (原值: {t['target']})", t['target'])

    # Message
    message = get_input(f"💬 发送的消息 (原值: {t['message']})", t['message'])

    # Interval
    interval_str = get_input(f"⏰ 间隔天数 (原值: {t['interval_days']})", str(t['interval_days']))
    try:
        interval_days = int(interval_str)
    except ValueError:
        print("⚠️ 输入无效，保留原间隔天数")
        interval_days = t['interval_days']

    # Topic ID
    orig_topic = str(t.get("topic_id", ""))
    topic_id_str = get_input(
        f"🧵 话题 ID (原值: {orig_topic if orig_topic else '无'}, 输入 none 清除)",
        orig_topic
    )

    # 组装修改
    t["target"] = target
    t["message"] = message
    t["interval_days"] = interval_days

    if topic_id_str.lower() == "none" or not topic_id_str.strip():
        t.pop("topic_id", None)
    else:
        try:
            t["topic_id"] = int(topic_id_str)
        except ValueError:
            print("⚠️ 话题 ID 必须是数字，保留原话题 ID")

    print(f"✅ 第 {idx + 1} 个目标修改成功！")


def delete_target(targets):
    """删除目标"""
    print_targets(targets)
    if not targets:
        return

    try:
        idx_str = get_input(f"请输入要删除的目标序号 (1-{len(targets)}) [直接回车返回菜单]")
        if not idx_str:
            return
        idx = int(idx_str) - 1
        if idx < 0 or idx >= len(targets):
            print("❌ 序号超出范围！")
            return
    except ValueError:
        print("❌ 输入无效！")
        return

    removed = targets.pop(idx)
    print(f"🗑️ 已成功删除目标: {removed['target']}")


def auto_add_to_gitignore():
    """直接且自动将 targets.key 追加写入 .gitignore"""
    gitignore_path = ".gitignore"
    rule = "targets.key"

    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # 判断是否已存在此规则
            exists = any(line.strip() == rule for line in lines)
            if not exists:
                with open(gitignore_path, "a", encoding="utf-8") as f:
                    # 如果原文件结尾没有换行，先补换行
                    if lines and not lines[-1].endswith("\n"):
                        f.write("\n")
                    f.write(f"{rule}\n")
                print("💾 已自动将 targets.key 追加写入 .gitignore 文件中。")
        except Exception as e:
            print(f"⚠️ 自动写入 .gitignore 失败: {e}")
    else:
        try:
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write(f"{rule}\n")
            print("💾 已创建 .gitignore 文件并自动写入 targets.key。")
        except Exception as e:
            print(f"⚠️ 自动创建并写入 .gitignore 失败: {e}")


def main():
    print("=========================================")
    print("       TARGETS_CONFIG 加密配置文件生成器       ")
    print("=========================================")

    targets = []
    current_key = None

    # 1. 检测是否存在已有加密配置
    if os.path.exists(ENCRYPTED_FILE):
        print(f"\n📢 检测到本地已存在加密配置文件 {ENCRYPTED_FILE}")
        choice = get_input("❓ 是否解密并读取现有配置进行修改？(Y/n)", "Y")
        if choice.lower() == "y":
            # 尝试加载密钥
            key_candidate = ""
            if os.path.exists(KEY_FILE):
                try:
                    with open(KEY_FILE, "r", encoding="utf-8") as f:
                        key_candidate = f.read().strip()
                except Exception:
                    pass

            if key_candidate:
                print(f"🔑 已自动加载本地密钥文件 {KEY_FILE}")
            else:
                key_candidate = get_input("🔑 请手动输入您的解密密钥 (Fernet AES 密钥)")

            if key_candidate:
                try:
                    with open(ENCRYPTED_FILE, "r", encoding="utf-8") as f:
                        encrypted_data = f.read().strip()
                    fernet = Fernet(key_candidate.encode())
                    decrypted_data = fernet.decrypt(encrypted_data.encode()).decode("utf-8")
                    targets = json.loads(decrypted_data)
                    current_key = key_candidate
                    print("✅ 解密读取配置成功！")
                except Exception as e:
                    print(f"❌ 解密失败，密钥错误或数据损坏：{e}")
                    print("⚠️ 将开启全新配置。")
            else:
                print("⚠️ 未提供密钥，将开启全新配置。")

    # 2. 如果是全新配置，提示输入至少一个目标
    if not targets:
        print("\n📝 正在初始化全新签到配置...")
        add_target(targets)

    # 3. 主交互循环菜单
    while True:
        print("\n--- 交互主菜单 ---")
        print("1. 查看当前所有目标配置")
        print("2. 添加新目标")
        print("3. 修改现有目标")
        print("4. 删除现有目标")
        print("5. 保存并退出")
        
        opt = get_input("请选择操作 (1-5)", "1")

        if opt == "1":
            print_targets(targets)
        elif opt == "2":
            add_target(targets)
        elif opt == "3":
            edit_target(targets)
        elif opt == "4":
            delete_target(targets)
        elif opt == "5":
            if not targets:
                print("❌ 目标列表为空，请至少添加一个目标！")
                continue
            break
        else:
            print("❌ 无效的选项，请重新选择！")

    # 4. 密钥生成与加密保存
    print("\n=========================================")
    print("💾 正在准备保存加密配置文件...")
    print("=========================================")

    # 检查密钥
    if not current_key:
        print("\n🔑 这是一个全新的配置，需要生成加密密钥。")
        save_key_opt = get_input("❓ 是否自动生成高强度的随机 AES 密钥并保存到本地 targets.key 文件？(Y/n)", "Y")
        
        if save_key_opt.lower() == "y":
            current_key = Fernet.generate_key().decode()
            try:
                with open(KEY_FILE, "w", encoding="utf-8") as f:
                    f.write(current_key)
                print(f"✅ 密钥已自动生成并保存至本地文件: {KEY_FILE}")
                
                # 自动且直接追加到 .gitignore
                auto_add_to_gitignore()
                
            except Exception as e:
                print(f"❌ 自动保存密钥文件失败: {e}")
                sys.exit(1)
        else:
            current_key = get_input("🔑 请手动输入您的 32 字节 Fernet AES 密钥 (需 Base64 编码)")
            while not current_key:
                print("❌ 密钥不能为空！")
                current_key = get_input("🔑 请手动输入密钥")

    # 执行加密并写入 enc 文件
    try:
        compact_json = json.dumps(targets, ensure_ascii=False, separators=(",", ":"))
        fernet = Fernet(current_key.encode())
        encrypted_bytes = fernet.encrypt(compact_json.encode("utf-8"))
        
        with open(ENCRYPTED_FILE, "w", encoding="utf-8") as f:
            f.write(encrypted_bytes.decode("utf-8"))
            
        print(f"\n🎉 成功！加密配置文件已保存为: {ENCRYPTED_FILE}")
        print("-----------------------------------------")
        print("📢 【安全提示与后续操作步骤】：")
        print(f"1. 您的本地密钥已成功生成并安全地存放在: {KEY_FILE}")
        print("2. 密钥已通过直接写入的方式自动加入了 .gitignore，以确保绝不会被误提交至仓库。")
        print("3. 当您在本地运行 `checkin.py` 时，脚本将自动加载 `targets.key` 执行解密，无需任何环境变量。")
        print("4. 如果在 GitHub Actions 中运行，请将以下密钥内容添加至您的 Repository Secrets，并命名为 `TARGETS_KEY`：")
        print(f"   🔑 您的密钥内容： {current_key}")
        print(f"5. 记得将加密的 `{ENCRYPTED_FILE}` 配置文件提交并推送至您的 GitHub 仓库。")
        print("=========================================")

    except Exception as e:
        print(f"❌ 配置文件加密保存失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消操作。")
