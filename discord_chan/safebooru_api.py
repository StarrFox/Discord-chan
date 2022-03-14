#  Copyright © 2022 SirOlaf
#
#  Discord Chan is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Discord Chan is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with Discord Chan.  If not, see <https://www.gnu.org/licenses/>.

import random
import urllib.parse
import xml.etree.ElementTree
from typing import Optional, List

import aiohttp


SAFEBOORU_BASE_URL = "https://safebooru.org/index.php?page=dapi&s=post&q=index"
# SUBTRACTIVE_NSFW_TAGS = ["-panties", "-underwear", "-bra", "-bikini", "-ass", "-exercise", "-sweat",
#                          "-topless", "-bare_back", "-mind_control", "-clothes_lift", "-squatting",
#                          "-bodysuit", "-micro_bra", "-bdsm", "-sexually_suggestive", "-suggestive_fluid",
#                          "-blood", "-poop", "-large_breasts", "-spread_legs", "-gigantic_breasts", "-crossdressing",
#                          "-nude", "-convenient_censoring", "-latex", "-topless_male", "-crop_top", "-skirt_pull",
#                          "-no_panties", "-stomach_cutout", "-undersized_clothing", "-nipples", "-skin_tight",
#                          "-groin", "-yuri", "-yaoi", "-french_kiss", "-swimsuit", "-convenient_leg", "-tagme"]

SUBTRACTIVE_NSFW_TAGS = ["-blood", "-poop", "-tagme"]


def join_safebooru_tags(tags: List[str]) -> str:
    return "+".join([urllib.parse.quote(x) for x in tags])


async def get_safebooru_post_count(tags: List[str]) -> Optional[int]:
    async with aiohttp.ClientSession() as session:
        async with session.get(SAFEBOORU_BASE_URL + f"&limit=0&tags={join_safebooru_tags(tags + SUBTRACTIVE_NSFW_TAGS)}") as resp:
            if resp.status == 200:
                tree = xml.etree.ElementTree.fromstring(await resp.content.read())
                if amount := tree.get("count"):
                    return int(amount)


async def get_safebooru_posts(tags: List[str], page: int=0) -> List[str]:
    result = []

    async with aiohttp.ClientSession() as session:
        async with session.get(SAFEBOORU_BASE_URL + f"&pid={page}&tags={join_safebooru_tags(tags + SUBTRACTIVE_NSFW_TAGS)}") as resp:
            if resp.status == 200:
                tree = xml.etree.ElementTree.fromstring(await resp.content.read())

                for post in tree:
                    if post_url := post.get("file_url"):
                        result.append(post_url)

            return result


async def get_random_safebooru_post(tags: List[str]) -> Optional[str]:
    if post_count := await get_safebooru_post_count(tags):
        page = random.randint(0, int(post_count / 100))

        posts = await get_safebooru_posts(tags, page)
        post_count = len(posts)
        if post_count > 0:
            return posts[random.randint(0, post_count-1)]
