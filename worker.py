# worker.py
# 后台工作线程
# 持续轮询数据库，发现 pending 任务就取出来处理，处理完更新状态为 done 或 failed
# 没有任务时休眠 10 秒再轮询

import time
from database import fetch_pending, update_status
from processing import process_image_file
from storage import save_processed_image

def worker_loop():
    while True:
        row = fetch_pending()
        if row:
            image_id = row["id"]
            original_path = row["original_path"]
            update_status(image_id, "processing")

            try:
                processed_img = process_image_file(original_path)
                if processed_img is None:
                    raise ValueError("图片读取失败")

                processed_path = save_processed_image(processed_img, original_path)
                update_status(image_id, "done", processed_path)

            except Exception as e:
                print(f"处理失败 id={image_id}: {e}")
                update_status(image_id, "failed")
        else:
            time.sleep(10)