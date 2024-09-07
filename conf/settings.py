from dotenv import load_dotenv
import os
import conf.global_values as g


def get_env_variable(var_name):
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"{var_name} is not set")
    return value


def load_env():
    load_dotenv()
    g.HOST_NAME = get_env_variable("HOST_NAME")
    g.USER_NAME = get_env_variable("USER_NAME")
    g.PASSWORD = get_env_variable("PASSWORD")
    g.WEBHOOK_URL = get_env_variable("WEBHOOK_URL")
