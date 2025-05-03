import json
import time

from praw.models import Submission

from utils import settings
from utils.console import print_step


def check_done(
    redditobj: Submission,
) -> Submission:
    # don't set this to be run anyplace that isn't subreddit.py bc of inspect stack
    """Checks if the chosen post has already been generated

    Args:
        redditobj (Submission): Reddit object gotten from reddit/subreddit.py

    Returns:
        Submission|None: Reddit object in args
    """
    with open("./video_creation/data/videos.json", "r", encoding="utf-8") as done_vids_raw:
        done_videos = json.load(done_vids_raw)
    for video in done_videos:
        if video["id"] == str(redditobj):
            if settings.config["reddit"]["thread"]["post_id"]:
                print_step(
                    "You already have done this video but since it was declared specifically in the config file the program will continue"
                )
                return redditobj
            print_step("Getting new post as the current one has already been done")
            return None
    return redditobj


def save_data(
    subreddit: str,
    filename: str,
    reddit_title: str,
    reddit_id: str,
    credit: str,
    author: str,
    upvotes: int,
    num_comments: int,
    ai_caption: str = ""
):
    """Saves the videos that have already been generated to a JSON file in video_creation/data/videos.json

    Args:
        subreddit (str): Name of the subreddit
        filename (str): The finished video title name
        reddit_title (str): Original Reddit title
        reddit_id (str): Reddit post ID
        credit (str): Background credit
        author (str): Reddit author
        upvotes (int): Number of upvotes
        num_comments (int): Number of comments read
        ai_caption (str): Optional AI-generated social caption
    """
    path = "./video_creation/data/videos.json"
    # Open file for read+write, update in-memory list, then overwrite & truncate
    with open(path, "r+", encoding="utf-8") as raw_vids:
        done_vids = json.load(raw_vids)

        # If this reddit_id already exists, do nothing
        if reddit_id in [video["id"] for video in done_vids]:
            return  # video already done but was specified to continue anyway in the config file

        # Build payload including new ai_caption field
        payload = {
            "subreddit": subreddit,
            "id": reddit_id,
            "time": str(int(time.time())),
            "background_credit": credit,
            "reddit_title": reddit_title,
            "filename": filename,
            "author": author,
            "upvotes": upvotes,
            "num_comments": num_comments,
            "ai_caption": ai_caption,  # newly added
        }
        done_vids.append(payload)

        # Write back and truncate to remove any leftover data
        raw_vids.seek(0)
        json.dump(done_vids, raw_vids, ensure_ascii=False, indent=4)
        raw_vids.truncate()
