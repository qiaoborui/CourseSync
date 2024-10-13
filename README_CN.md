# 课程日历订阅

[English](README.md) | 中文

## 项目简介

这是一个为大学生设计的日历订阅应用。该应用允许学生轻松地将学校的课程表、考试安排和其他重要事件同步到他们的个人日历中。

目前支持学校:
- 西安建筑科技大学
- 西北农林科技大学

## 主要功能

- 自动同步XAUAT和NWAFU学生课程表
- 导入考试安排和学校重要日期
- 支持多种日历应用(如Google日历、Apple日历、Outlook等)
- 实时更新，确保信息始终保持最新

## 如何使用

1. 访问我们的网页应用: [calendar-subscription-app.html](https://schedule.borry.org/)
2. 选择你的学校
3. 使用你的学生账号登录
4. 点击"点击订阅"按钮
5. 将生成的链接添加到你喜欢的日历应用中

## 贡献指南

我们欢迎并感谢任何形式的贡献！以下是一些参与项目的方式：

### 报告问题

如果你发现了bug或有新功能建议，请在GitHub上创建一个issue。请确保提供以下信息：

- 问题的详细描述
- 重现问题的步骤（如果适用）
- 预期行为和实际行为
- 截图（如果有助于说明问题）

### 提交代码

1. Fork 这个仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的改动 (`git commit -m 'Add some AmazingFeature'`)
4. 将你的改动推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个Pull Request

### 代码风格

- 对于Python代码，请遵循PEP 8规范
- 对于JavaScript/HTML/CSS，请使用2空格缩进
- 确保你的代码有适当的注释

### 添加新学校支持

如果你想为新的学校添加支持，请遵循以下步骤：

1. 在`backend/school`目录下创建一个新的文件夹，以学校名称命名
2. 在新创建的文件夹中实现`*_client.py`文件，继承`BaseAcademicSystemClient`类
3. 实现所有必要的方法，包括认证、获取课程和考试信息等
4. 在`web/index.html`文件中的学校选择下拉菜单中添加新学校选项

### 测试

- 在提交PR之前，请确保所有现有的测试都能通过
- 如果你添加了新功能，请为其编写相应的测试

感谢你对项目的贡献！
