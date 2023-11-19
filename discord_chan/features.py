from enum import Enum

from .database import Database


class Feature(Enum):
    word_track = 1
    typing_watch = 2
    gamer_words = 3
    cope = 4


class FeatureManager:
    def __init__(self, database: Database) -> None:
        self.database = database

        self.cache: dict[int, list[str]] = {}

    async def _refresh_cache(self, guild_id: int):
        # note: empty list is accepted
        self.cache[guild_id] = await self.database.get_guild_enabled_features(guild_id)

    async def is_enabled(self, feature: Feature, guild_id: int) -> bool:
        feature_string = feature.name

        if self.cache.get(guild_id):
            return feature_string in self.cache[guild_id]

        await self._refresh_cache(guild_id)
        return feature_string in self.cache[guild_id]

    async def set_enabled(self, feature: Feature, guild_id: int):
        await self.database.enable_guild_enabled_feature(guild_id, feature.name)
        await self._refresh_cache(guild_id)

    async def set_disabled(self, feature: Feature, guild_id: int):
        await self.database.disable_guild_enabled_feature(guild_id, feature.name)
        await self._refresh_cache(guild_id)

    async def toggle(self, feature: Feature, guild_id: int):
        if await self.is_enabled(feature, guild_id):
            await self.set_disabled(feature, guild_id)
            return False
        else:
            await self.set_enabled(feature, guild_id)
            return True

    async def get_status(self, guild_id: int) -> tuple[list[Feature], list[Feature]]:
        await self._refresh_cache(guild_id)

        enabled: list[Feature] = []
        disabled: list[Feature] = []

        for feature in Feature:
            if feature.name in self.cache[guild_id]:
                enabled.append(feature)
            else:
                disabled.append(feature)

        return enabled, disabled
