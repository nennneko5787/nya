import os
import json

import asyncpg
import dotenv

from aiopaypaython import PayPay
from aiokyasher import Kyash

from typing import Dict

dotenv.load_dotenv()


class Database:
    pool: asyncpg.Pool = None
    paypay: PayPay = None
    kyash: Kyash = None

    @classmethod
    async def initialize(cls):
        cls.pool = await asyncpg.create_pool(os.getenv("dsn"), statement_cache_size=0)
        with open("./credentials.json") as f:
            data: Dict[str, Dict[str, str]] = json.load(f)
        cls.paypay = PayPay()
        if not data["paypay"]["accessToken"]:
            if not data["paypay"]["clientUUID"]:
                await cls.paypay.initialize(
                    data["paypay"]["phone"],
                    data["paypay"]["password"],
                )
                await cls.paypay.login(input("OTP: "))
            else:
                await cls.paypay.initialize(
                    data["paypay"]["phone"],
                    data["paypay"]["password"],
                    data["paypay"]["deviceUUID"],
                    data["paypay"]["clientUUID"],
                )
        else:
            await cls.paypay.initialize(access_token=data["paypay"]["accessToken"])
            try:
                await cls.paypay.get_balance()
            except:
                await cls.paypay.token_refresh(data["paypay"]["refreshToken"])

        data["paypay"]["deviceUUID"] = cls.paypay.device_uuid
        data["paypay"]["clientUUID"] = cls.paypay.client_uuid
        data["paypay"]["accessToken"] = cls.paypay.access_token
        try:
            data["paypay"]["refreshToken"] = cls.paypay.refresh_token
        except:
            pass

        with open("./credentials.json", "r+") as f:
            json.dump(data, f)

        cls.kyash = Kyash()
        if not data["kyash"]["clientUUID"]:
            await cls.kyash.login(
                data["kyash"]["email"],
                data["kyash"]["password"],
            )
        else:
            await cls.kyash.login(
                data["kyash"]["email"],
                data["kyash"]["password"],
                data["kyash"]["clientUUID"],
                data["kyash"]["installationUUID"],
            )

        if not cls.kyash.access_token:
            await cls.kyash.validate_otp(input("OTP: "))

        data["kyash"]["installationUUID"] = cls.kyash.installation_uuid
        data["kyash"]["clientUUID"] = cls.kyash.client_uuid

        with open("./credentials.json", "r+") as f:
            json.dump(data, f)
