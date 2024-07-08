from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Chart(models.Model):
    """
    {
      title: '图表示例',
      xAxis: ["衬衫", "羊毛衫", "雪纺衫", "裤子", "高跟鞋", "袜子"],
      eries: [
		{ name: '销量', data: [5, 20, 36, 10, 10, 20] },
		{ name: '销量2', data: [51, 0, 6, 1, 101, 22] }
	]
}
    """
    chart_types = (
        (1, '柱状图'),
        (2, '饼图'),
    )
    chart = models.JSONField(default=dict, verbose_name='图表', blank=True, null=True)
    chart_type = models.IntegerField(choices=chart_types, default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户', related_name='charts')
