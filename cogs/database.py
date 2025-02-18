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
        paypay = PayPay()
        if not data["paypay"]["accessToken"]:
            if not data["paypay"]["clientUUID"]:
                await paypay.initialize(
                    data["paypay"]["phone"],
                    data["paypay"]["password"],
                )
            else:
                await paypay.initialize(
                    data["paypay"]["phone"],
                    data["paypay"]["password"],
                    data["paypay"]["deviceUUID"],
                    data["paypay"]["clientUUID"],
                )
            await paypay.login(input("OTP: "))
        else:
            await paypay.initialize(access_token=data["paypay"]["accessToken"])
            try:
                await paypay.get_balance()
            except:
                await paypay.token_refresh(data["paypay"]["refreshToken"])

        data["paypay"]["deviceUUID"] = paypay.device_uuid
        data["paypay"]["clientUUID"] = paypay.client_uuid
        data["paypay"]["accessToken"] = paypay.access_token
        try:
            data["paypay"]["refreshToken"] = paypay.refresh_token
        except:
            pass

        with open("./credentials.json", "r+") as f:
            json.dump(data, f)

        kyash = Kyash()
        if not data["kyash"]["clientUUID"]:
            await kyash.login(
                data["kyash"]["email"],
                data["kyash"]["password"],
            )
        else:
            await kyash.login(
                data["kyash"]["email"],
                data["kyash"]["password"],
                data["kyash"]["clientUUID"],
                data["kyash"]["installationUUID"],
            )

        if not kyash.access_token:
            await kyash.validate_otp(input("OTP: "))

        data["kyash"]["installationUUID"] = kyash.installation_uuid
        data["kyash"]["clientUUID"] = kyash.client_uuid

        with open("./credentials.json", "r+") as f:
            json.dump(data, f)
