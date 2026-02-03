#!/usr/bin/env python3
"""
Batch Image Resizer & Converter
-------------------------------
画像を一括でリサイズ・WebP/JPEG変換するツール。
フォルダごとの一括処理、ドラッグ＆ドロップ、CLI引数の両方に対応。

Usage:
    python resize.py [inputs...] [-w width] [-t type]
"""

import argparse
import shlex
import sys
from pathlib import Path
from PIL import Image

# 対応する拡張子
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

def get_unique_filepath(directory: Path, filename: str) -> Path:
    """同名ファイルがある場合、連番を付与して重複を回避する"""
    file_path = directory / filename
    if not file_path.exists():
        return file_path

    stem = file_path.stem
    suffix = file_path.suffix
    counter = 1

    while True:
        new_filename = f"{stem}_{counter}{suffix}"
        new_path = directory / new_filename
        if not new_path.exists():
            return new_path
        counter += 1

def process_images(path_strings, max_width, mode_type):
    """メイン処理ロジック"""

    # --- 設定 ---
    if mode_type in ["webp", "w"]:
        save_format = "WebP"
        save_extension = ".webp"
        output_folder_name = "webp"
    else:
        save_format = "JPEG"
        save_extension = ".jpg"
        output_folder_name = "jpg"

    target_files = []

    # --- 画像の収集 ---
    print(f"🔍 解析中...")
    for p_str in path_strings:
        clean_path = p_str.strip('"').strip("'")
        if not clean_path: continue

        path_obj = Path(clean_path)

        if path_obj.is_dir():
            # フォルダなら再帰的ではなく直下のみ検索（必要なら rglob に変更可）
            for child in path_obj.iterdir():
                if child.is_file() and child.suffix.lower() in IMAGE_EXTENSIONS:
                    target_files.append(child)
        elif path_obj.is_file():
            if path_obj.suffix.lower() in IMAGE_EXTENSIONS:
                target_files.append(path_obj)
        else:
            print(f"⚠️ 無視: {clean_path} (存在しないか対象外)")

    if not target_files:
        print("❌ 処理可能な画像が見つかりませんでした。")
        return

    print(f"🚀 {len(target_files)} 枚の画像を処理します... (幅: {max_width}px, 形式: {save_format})")

    # --- 変換実行 ---
    success_count = 0
    for image_path in target_files:
        try:
            # 出力フォルダ作成
            output_dir = image_path.parent / output_folder_name
            output_dir.mkdir(exist_ok=True)

            with Image.open(image_path) as img:
                img = img.convert("RGB")

                # リサイズ
                width, height = img.size
                if width > max_width:
                    new_height = int((max_width / width) * height)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                # 保存パス決定（上書き防止）
                output_path = get_unique_filepath(output_dir, image_path.stem + save_extension)

                # 保存
                if save_format == "WebP":
                    img.save(output_path, format="WebP", quality=80, method=6)
                else:
                    img.save(output_path, format="JPEG", quality=80)

                # ログ
                if output_path.stem != image_path.stem and output_path.stem.split('_')[-1].isdigit():
                     print(f"✅ 保存: {output_path.name} (連番付与)")
                else:
                     print(f"✅ 保存: {output_path.name}")

                success_count += 1

        except Exception as e:
            print(f"❌ エラー ({image_path.name}): {e}")

    print(f"🎉 完了! ({success_count}/{len(target_files)} 枚成功)\n")

def main():
    parser = argparse.ArgumentParser(description="Python製 画像一括リサイズ＆形式変換ツール")
    parser.add_argument("inputs", nargs="*", help="入力ファイルまたはフォルダのパス")
    parser.add_argument("-w", "--width", type=int, default=1200, help="リサイズする最大横幅 (デフォルト: 1200)")
    parser.add_argument("-t", "--type", choices=["jpeg", "jpg", "webp"], default="jpeg", help="出力形式 (jpeg または webp)")

    args = parser.parse_args()

    # 引数がある場合はワンショット実行
    if args.inputs:
        process_images(args.inputs, args.width, args.type)
        return

    # 引数がない場合は対話モード
    print(f"\n--- 🛠️  対話モード (設定: 幅{args.width}px / 形式{args.type}) ---")
    print("終了するには 'q' を入力してください。")
    print("-" * 60)

    try:
        while True:
            input_str = input("【フォルダ】または【画像ファイル】をドラッグ＆ドロップしてください\n>> ").strip()

            if not input_str or input_str.lower() in ["q", "quit", "exit"]:
                print("👋 終了します。")
                break

            try:
                path_strings = shlex.split(input_str)
                process_images(path_strings, args.width, args.type)
                print("-" * 60)
            except ValueError:
                print("❌ パスの解析に失敗しました。\n")

    except KeyboardInterrupt:
        print("\n👋 終了します。")

if __name__ == "__main__":
    main()
