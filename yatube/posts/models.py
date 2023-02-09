from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
CHARS_TO_OUTPUT = 15


class Group(models.Model):
    title = models.CharField("Имя", max_length=200,
                             help_text="Введите название группы")
    slug = models.SlugField("Адрес", unique=True)
    description = models.TextField("Описание",
                                   help_text="Введите краткое описание группы")

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField("Текст поста", help_text="Введите текст "
                                                     "публикации")
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True,
                                    db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="posts",
                               verbose_name="Автор"
                               )
    group = models.ForeignKey(Group, blank=True,
                              null=True, on_delete=models.SET_NULL,
                              related_name="posts",
                              verbose_name="Сообщество",
                              help_text=("Сообщение будет относиться к этой "
                                         "группе")
                              )
    image = models.ImageField(
        "Добоавьте картинку",
        upload_to="posts/",
        blank=True
    )

    def __str__(self):
        return self.text[:CHARS_TO_OUTPUT]

    def text50_for_admin(self):
        if len(self.text) > 50:
            return f"{self.text[:50]}..."
        return self.text

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Пост"
        verbose_name_plural = "Посты"


class Comment(models.Model):
    post = models.ForeignKey(Post, blank=False,
                             null=False, on_delete=models.CASCADE,
                             related_name="comment"
                             )
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="comment",
                               verbose_name="Автор"
                               )
    text = models.TextField("Комментарий", blank=False,
                            null=False,
                            help_text=("Оставьте свой комментарий"))
    created = models.DateTimeField("Дата комментария", auto_now_add=True)

    def __str__(self):
        return self.text[:CHARS_TO_OUTPUT]

    def text50_for_admin(self):
        if len(self.text) > 50:
            return f"{self.text[:50]}..."
        return self.text

    class Meta:
        ordering = ["-created"]
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="follower",
                             verbose_name="Подписчик"
                             )
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="following",
                               verbose_name="Автор"
                               )
