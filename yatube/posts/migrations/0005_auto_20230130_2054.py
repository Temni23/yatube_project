# Generated by Django 2.2.16 on 2023-01-30 13:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0004_auto_20221218_1535"),
    ]

    operations = [
        migrations.AlterField(
            model_name="group",
            name="description",
            field=models.TextField(help_text="Введите краткое описание группы",
                                   verbose_name="Описание"),
        ),
        migrations.AlterField(
            model_name="group",
            name="title",
            field=models.CharField(help_text="Введите название группы",
                                   max_length=200, verbose_name="Имя"),
        ),
        migrations.AlterField(
            model_name="post",
            name="group",
            field=models.ForeignKey(blank=True,
                                    help_text="Сообщение будет относиться к этой группе",
                                    null=True,
                                    on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="posts", to="posts.Group",
                                    verbose_name="Сообщество"),
        ),
        migrations.AlterField(
            model_name="post",
            name="text",
            field=models.TextField(help_text="Введите текст публикации",
                                   verbose_name="Текст"),
        ),
    ]
