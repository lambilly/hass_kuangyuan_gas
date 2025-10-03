# 旷远燃气 Home Assistant 集成

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

这是一个用于 Home Assistant 的自定义集成，用于查询旷远燃气的余额、用气量等信息。

## 功能特性

- 查询燃气费余额
- 查询累积用气量
- 查询是否通气状态
- 查询数据更新时间
- 自动24小时更新数据

## 安装方法
### 方法一：通过 HACS 安装（推荐）
1. 确保已安装 [HACS](https://hacs.xyz/)
2. 在 HACS 的 "Integrations" 页面，点击右上角的三个点菜单，选择 "Custom repositories"
3. 在弹出窗口中添加仓库地址：https://github.com/lambilly/hass_kuangyuan_gas，类别选择 "Integration"
4. 在 HACS 中搜索「旷远燃气」
5. 点击下载
6. 重启 Home Assistant

### 方法二：手动安装
1. 下载本集成文件
2. 将 `custom_components/kuangyuan_gas` 文件夹复制到您的 Home Assistant 配置目录中的 `custom_components` 文件夹内
3. 重启 Home Assistant

### 通过 UI 配置

1. 进入 Home Assistant 「配置」->「设备与服务」
2. 点击「+ 添加集成」
3. 搜索「旷远燃气」
4. 按照提示输入以下信息：
   - **燃气户号**: 您的燃气账户号（如 KYNYN094877）
   - **Cookie**: 从浏览器获取的 Cookie（不含手机号部分）
   - **手机号**: 您的手机号码

### 如何获取 Cookie

1. 登录 [旷远燃气官网](http://www.kynyyyt.com)
2. 打开浏览器开发者工具（F12）
3. 切换到「网络」标签
4. 刷新页面或进行任意操作
5. 找到任意请求，复制 `Cookie` 请求头的值
6. 只复制 Cookie 中不包含手机号的部分

## 实体

安装成功后，将创建以下传感器实体：

| 实体名称 | 类型 | 单位 | 图标 |
|---------|------|------|------|
| 燃气费余额 | 数值传感器 | 元 | mdi:currency-cny |
| 累积用气量 | 气体传感器 | m³ | mdi:meter-gas-outline |
| 是否通气 | 状态传感器 | - | mdi:pipe-valve |
| 截至时间 | 时间传感器 | - | mdi:update |

## 故障排除

### 实体显示「不可用」

1. 检查网络连接
2. 验证燃气户号、Cookie 和手机号是否正确
3. 检查 Cookie 是否已过期（需要重新获取）

### 数据不更新

1. 集成默认每24小时自动更新一次
2. 可以手动调用 `homeassistant.update_entity` 服务强制更新

## 支持

如有问题，请通过以下方式联系：
- 创建 [GitHub Issue](https://github.com/lambilly/hass_kuangyuan_gas/issues)
- 发送邮件至作者

## 许可证

MIT License

## 更新日志

### v1.0.0
- 初始版本发布
- 支持燃气费余额、用气量等数据查询
