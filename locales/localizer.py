from locales import uk
import logging

logger = logging.getLogger("localizer")
SUPPORTED_LANGUAGE = "uk"


class Localizer:
    def __new__(cls, curr_lang: str | None = None):
        if not hasattr(cls, "instance"):
            cls.instance = super(Localizer, cls).__new__(cls)
            cls.instance.languages = {
                "uk": uk
            }
            cls.instance.current_language = SUPPORTED_LANGUAGE
        cls.instance.current_language = SUPPORTED_LANGUAGE
        return cls.instance

    def translate(self, variable_name: str, *args, language: str | None = None):
        """
        Повертає форматований локалізований текст українською.

        :param variable_name: название переменной с текстом.
        :param args: аргументы для форматирования.
        :param language: залишено для сумісності з плагінами.

        :return: форматированный локализированный текст.
        """
        text = variable_name
        if hasattr(uk, variable_name):
            text = getattr(uk, variable_name)

        args = list(args)
        formats = text.count("{}")
        if len(args) < formats:
            args.extend(["{}"] * (formats - len(args)))
        try:
            return text.format(*args)
        except:
            logger.debug("TRACEBACK", exc_info=True)
            return text

    def add_translation(self, uuid: str, variable_name: str, value: str, language: str = "uk"):
        """Додає переклад фраз із плагіна в українську локаль."""
        setattr(uk, f"{uuid}_{variable_name}", value)

    def plugin_translate(self, uuid: str, variable_name: str, *args, language: str | None = None):
        """Повертає переклад фраз із плагіна українською."""
        s = f"{uuid}_{variable_name}"
        result = self.translate(s, *args, language=language)
        if result != s:
            return result
        else:
            return self.translate(variable_name, *args, language=language)
