from dataclasses import dataclass
from typing import Self

from botocore.exceptions import ClientError
from types_aiobotocore_s3.client import S3Client


class ObjectStorageError(Exception): ...


class ObjectNotFoundError(ObjectStorageError): ...


class ObjectExistsError(ObjectStorageError): ...


@dataclass
class ObjectBucket:
    client: S3Client
    name: str

    @classmethod
    async def create_if_needed(cls, client: S3Client, name: str) -> Self:
        obj = cls(client, name)

        try:
            await client.head_bucket(Bucket=name)
        except ClientError:
            await obj.create()

        return obj

    async def create(self):
        await self.client.create_bucket(Bucket=self.name)

    async def delete(self):
        await self.client.delete_bucket(Bucket=self.name)

    async def get_object(self, name: str):
        try:
            return await self.client.get_object(Bucket=self.name, Key=name)
        except ClientError as error:
            # amazon thought it would be really funny if their error types weren't real
            if error.__class__.__name__ == "NoSuchKey":
                return None

            # unaccounted for error
            raise error

    async def read_object(self, name: str) -> bytes:
        obj = await self.get_object(name)

        if obj is None:
            raise ObjectNotFoundError(f"{name=} not found")

        return await obj["Body"].read()

    async def put_object_unchecked(self, name: str, data: bytes, **kwargs):
        return await self.client.put_object(
            Bucket=self.name, Key=name, Body=data, **kwargs
        )

    async def put_object(
        self, name: str, data: bytes, *, allow_overwrite: bool = False, **kwargs
    ):
        potential_object = await self.get_object(name)

        if potential_object is not None and allow_overwrite is False:
            raise ObjectExistsError(f"{name=} already exists")

        await self.put_object_unchecked(name, data, **kwargs)


if __name__ == "__main__":
    from aiobotocore.session import get_session

    async def main():
        session = get_session()

        async with session.create_client(
            "s3",
            endpoint_url="http://192.168.1.184:9001",
            aws_access_key_id="main",
            aws_secret_access_key="XL7p672T5vm#TFQQWn",
        ) as s3:
            bucket = await ObjectBucket.create_if_needed(s3, "dcpfp")

            await bucket.put_object_unchecked("123", b"456")

            obj = await bucket.get_object("123")
            print(f"{obj=}")

            data = await bucket.read_object("123")
            print(f"{data=}")

    import asyncio

    asyncio.run(main())
