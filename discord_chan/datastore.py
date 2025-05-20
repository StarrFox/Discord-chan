from __future__ import annotations

import zlib
import json
from pathlib import Path
from typing import Self

from loguru import logger

"""

store.store(bytes=b"") -> DataKey(92384792384) ~~ 0x92384792384
store.store(DataFile(name="...", data=...))

store.store(b"")


store = await DataStore.from_name("main")
pfps_group = await store.get_group("pfps", settings=DataGroupSettings(max_usage=DataSize(GB=20), key_max_usage=DataSize(MB=200)))
snipe_group = await store.get_group("snipes", settings=DataGroupSettings(max_usage=DataSize(GB=20)))



stores/
--[store name]/
----references.json
----data/
------92384792384.data
----[substore name]/
"""


RESERVED_NAMES = (
    "data",
    "references.json"
)


# TODO: add data usage settings
class DataStore:
    def __init__(self, *, file_path: Path, name: str, parent: Self | None = None) -> None:
        self.file_path = file_path
        self.name = name
        self.parent = parent

        self._checked_out_substores: dict[str, Self] = {}
        self._references: dict[int, int] | None = None
        self._qualified_name: str | None = None

    @classmethod
    def from_root(cls, root_path: Path, name: str) -> Self:
        return cls(file_path=root_path / name, name=name)

    def get_substore(self, name: str) -> Self:
        if (substore := self._checked_out_substores.get(name)) is not None:
            return substore

        substore = type(self)(file_path=self.file_path / name, name=name, parent=self)
        self._checked_out_substores[name] = substore
        return substore

    def get_qualified_name(self) -> str:
        if self._qualified_name is not None:
            return self._qualified_name

        if self.parent is not None:
            self._qualified_name = f"{self.parent.get_qualified_name()}.{self.name}"
        else:
            self._qualified_name = self.name

        return self._qualified_name

    def _get_references(self) -> dict[int, int]:
        if self._references is not None:
            return self._references

        ref_path = self.file_path / "references.json"

        if not ref_path.exists():
            logger.debug(f"Creating reference info for {self.get_qualified_name()}")
            ref_path.touch()
            self._references = {}
            return self._references
        else:
            if not ref_path.is_file():
                raise RuntimeError(f"References file for {self.get_qualified_name()} is not a file")

            from_file: dict[str, int] = json.load(ref_path.open())
            try:
                self._references = dict(map(lambda kv: (int(kv[0]), kv[1]), from_file.items()))
            except ValueError:
                raise RuntimeError(f"References file for {self.get_qualified_name()} corrupted")
            return self._references

    def _save_references(self, references: dict[int, int]) -> None:
        ref_path = self.file_path / "references.json"

        if not ref_path.exists() or not ref_path.is_file():
            raise RuntimeError(f"_save_references called before _get_references for {self.get_qualified_name()}")

        json.dump(references, ref_path.open("w"))

    def _inc_ref(self, key: int):
        # TODO: maybe make references a context manager
        refs = self._get_references()

        if refs.get(key) is not None:
            refs[key] += 1
        else:
            # we start at 2 because we don't count 1s to save space
            refs[key] = 2
        
        self._save_references(refs)

    def _dec_ref(self, key: int, *, delay_save: bool = False) -> bool:
        refs = self._get_references()

        if refs.get(key) is not None:
            refs[key] -= 1

            should_delete = refs[key] <= 0
        else:
            # this means it was called for a file with 1 reference that was never stored
            return True

        if should_delete:
            del refs[key]

        # allow delaying for mass deletes
        if not delay_save:
            self._save_references(refs)

        return should_delete

    def get_key_references(self, key: int, *, check_exists: bool = False) -> int:
        refs = self._get_references()

        if (count := refs.get(key)) is not None:
            return count

        if check_exists:
            if not self.key_exists(key):
                return 0

        return 1

    def _create_key(self, data: bytes) -> tuple[bool, int]:
        key = zlib.crc32(data)

        if dupe := self.key_exists(key):
            self._inc_ref(key)
        
        return dupe, key

    def key_exists(self, key: int) -> bool:
        return (self.file_path / "data" / f"{key}.data").exists()

    def store(self, data: bytes) -> int:
        if not self.file_path.exists():
            logger.info(f"Datastore {self.get_qualified_name()} not found, creating")
            self.file_path.mkdir()
            (self.file_path / "data").mkdir()

        if not self.file_path.is_dir():
            raise RuntimeError(f"Datastore {self.get_qualified_name()} exists but is not a directory")

        duplicate, key = self._create_key(data)

        if duplicate:
            return key

        file_path = self.file_path / "data" / f"{key}.data"

        with open(file_path, "xb+") as fp:
            fp.write(data)

        return key



if __name__ == "__main__":
    store = DataStore.from_root(Path("."), name="test")
    key = store.store(b"uwu")

    substore = store.get_substore("sub")
    substore.store(b"bleb")

















