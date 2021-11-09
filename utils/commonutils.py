def snowflakeToTime(snowflake: int) -> int:
    return snowflake//4194304000 + 1420070400