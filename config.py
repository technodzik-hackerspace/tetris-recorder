from dynaconf import Dynaconf

settings = Dynaconf(
    environments=True,
    default_settings_paths=["settings.toml", ".secrets.toml"],
)
