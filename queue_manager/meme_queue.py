from datetime import time, datetime, timedelta

POSTING_TIMES = [
    time(hour=9, minute=0, second=0),
    time(hour=13, minute=0, second=0),
    time(hour=18, minute=0, second=0),
    time(hour=23, minute=0, second=0),
]


def manage_meme_queue(meme_current_queue: list, new_meme: dict) -> list:
    # Check if there are any memes in queue
    if len(meme_current_queue) == 0:
        # If there are no memes in post queue - add new one on corresponding time
        # Get appropriate time for posting
        present_date = datetime.now()
        present_time = present_date.time()
        for timestamp in POSTING_TIMES:
            if present_time < timestamp:
                # If present time is lesser, than timestamp in marked post time (e.x. 07:00 < 08:00)
                # than add this mew meme to queue and set post time to nearby time
                new_meme["post_time"] = datetime(
                    year=present_date.year, month=present_date.month, day=present_date.day,
                    hour=timestamp.hour, minute=timestamp.minute, second=timestamp.second
                ).strftime("%Y-%m-%d %H:%M:%S")
                meme_current_queue.append(new_meme)
                return meme_current_queue
    # If there are already memes in post queue
    # Get last meme in post queue post time
    last_meme_post_time: datetime = datetime.strptime(meme_current_queue[-1]["post_time"], "%Y-%m-%d %H:%M:%S")
    print(last_meme_post_time)
    tmp_post_time: datetime = last_meme_post_time
    # First, check if last meme post time is not final for that day (23:00)
    if last_meme_post_time.time() == POSTING_TIMES[-1]:
        # If True => set post time to next day at POSTING_TIMES[0] (09:00)
        tmp_post_time += timedelta(days=1)
        new_meme["post_time"] = datetime(
            year=tmp_post_time.year, month=tmp_post_time.month, day=tmp_post_time.day,
            hour=POSTING_TIMES[0].hour, minute=POSTING_TIMES[0].minute, second=POSTING_TIMES[0].second
        ).strftime("%Y-%m-%d %H:%M:%S")
        meme_current_queue.append(new_meme)
        return meme_current_queue
    if last_meme_post_time.time() != POSTING_TIMES[-1]:
        # Now find tha appropriate time slot from remaining times for that day (POSTING_TIMES[0:3])
        for queue_time in POSTING_TIMES:
            print(f"{last_meme_post_time.time()} : {queue_time}; {last_meme_post_time.time() >= queue_time}")
            if not last_meme_post_time.time() >= queue_time:
                new_meme["post_time"] = datetime(
                    year=last_meme_post_time.year, month=last_meme_post_time.month, day=last_meme_post_time.day,
                    hour=queue_time.hour, minute=queue_time.minute, second=queue_time.second
                ).strftime("%Y-%m-%d %H:%M:%S")
                meme_current_queue.append(new_meme)
                return meme_current_queue
