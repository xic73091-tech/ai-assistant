"""隐私保护模块测试"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.privacy import PrivacyProtector, SensitiveInfo


class TestPrivacyLevel:
    """测试隐私级别"""

    def test_default_level_medium(self):
        """默认隐私级别为medium"""
        with patch("src.privacy.config") as mock_config:
            mock_config.get_privacy_level.return_value = "medium"
            protector = PrivacyProtector()
            assert protector.level == "medium"

    def test_high_level_enables_all(self):
        """高级别启用所有检测"""
        protector = PrivacyProtector(level="high")
        assert "id_card" in protector.enabled_levels
        assert "phone" in protector.enabled_levels
        assert "email" in protector.enabled_levels
        assert "bank_card" in protector.enabled_levels
        assert "password" in protector.enabled_levels
        assert "ip_address" in protector.enabled_levels

    def test_medium_level_subset(self):
        """中级别启用部分检测"""
        protector = PrivacyProtector(level="medium")
        assert "id_card" in protector.enabled_levels
        assert "phone" in protector.enabled_levels
        assert "bank_card" in protector.enabled_levels
        assert "password" in protector.enabled_levels
        assert "email" not in protector.enabled_levels
        assert "ip_address" not in protector.enabled_levels

    def test_low_level_minimal(self):
        """低级别最少检测"""
        protector = PrivacyProtector(level="low")
        assert "id_card" in protector.enabled_levels
        assert "bank_card" in protector.enabled_levels
        assert "password" in protector.enabled_levels
        assert "phone" not in protector.enabled_levels
        assert "email" not in protector.enabled_levels

    @patch("src.privacy.config")
    def test_set_level(self, mock_config):
        """动态设置隐私级别"""
        protector = PrivacyProtector(level="low")
        protector.set_level("high")
        assert protector.level == "high"
        assert "email" in protector.enabled_levels
        mock_config.set_privacy_level.assert_called_once_with("high")

    def test_set_invalid_level(self):
        """设置无效级别抛出异常"""
        protector = PrivacyProtector(level="medium")
        with pytest.raises(ValueError, match="隐私级别必须是"):
            protector.set_level("ultra")

    def test_level_description(self):
        """获取级别描述"""
        for level in ("low", "medium", "high"):
            protector = PrivacyProtector(level=level)
            desc = protector.get_level_description()
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestPhoneDetection:
    """测试手机号检测"""

    def test_detect_chinese_phone(self):
        """检测中国手机号"""
        protector = PrivacyProtector(level="medium")
        results = protector.detect("我的手机号是13812345678")
        phone_results = [r for r in results if r.type == "phone"]
        assert len(phone_results) == 1
        assert phone_results[0].value == "13812345678"

    def test_detect_multiple_phones(self):
        """检测多个手机号"""
        protector = PrivacyProtector(level="medium")
        results = protector.detect("联系我13812345678或15987654321")
        phone_results = [r for r in results if r.type == "phone"]
        assert len(phone_results) == 2

    def test_phone_not_in_low_level(self):
        """低级别不检测手机号"""
        protector = PrivacyProtector(level="low")
        results = protector.detect("手机号13812345678")
        phone_results = [r for r in results if r.type == "phone"]
        assert len(phone_results) == 0

    def test_phone_mask_format(self):
        """手机号脱敏格式"""
        protector = PrivacyProtector(level="medium")
        results = protector.detect("13812345678")
        phone_results = [r for r in results if r.type == "phone"]
        assert len(phone_results) == 1
        assert phone_results[0].masked == "138****5678"

    def test_no_false_positive_short_number(self):
        """短数字不误报为手机号"""
        protector = PrivacyProtector(level="medium")
        results = protector.detect("数量是12345")
        phone_results = [r for r in results if r.type == "phone"]
        assert len(phone_results) == 0


class TestIdCardDetection:
    """测试身份证号检测"""

    def test_detect_id_card(self):
        """检测身份证号"""
        protector = PrivacyProtector(level="medium")
        results = protector.detect("身份证号110101199001011234")
        id_results = [r for r in results if r.type == "id_card"]
        assert len(id_results) == 1
        assert id_results[0].value == "110101199001011234"

    def test_id_card_mask_format(self):
        """身份证号脱敏格式"""
        protector = PrivacyProtector(level="medium")
        results = protector.detect("110101199001011234")
        id_results = [r for r in results if r.type == "id_card"]
        assert len(id_results) == 1
        masked = id_results[0].masked
        assert masked.startswith("110101")
        assert masked.endswith("1234")
        assert "********" in masked

    def test_id_card_with_x(self):
        """带X的身份证号"""
        protector = PrivacyProtector(level="medium")
        results = protector.detect("11010119900101123X")
        id_results = [r for r in results if r.type == "id_card"]
        assert len(id_results) == 1


class TestEmailDetection:
    """测试邮箱检测"""

    def test_detect_email(self):
        """检测邮箱"""
        protector = PrivacyProtector(level="high")
        results = protector.detect("我的邮箱test@example.com")
        email_results = [r for r in results if r.type == "email"]
        assert len(email_results) == 1
        assert email_results[0].value == "test@example.com"

    def test_email_not_in_medium_level(self):
        """中级别不检测邮箱"""
        protector = PrivacyProtector(level="medium")
        results = protector.detect("邮箱test@example.com")
        email_results = [r for r in results if r.type == "email"]
        assert len(email_results) == 0

    def test_email_mask_format(self):
        """邮箱脱敏格式"""
        protector = PrivacyProtector(level="high")
        results = protector.detect("test@example.com")
        email_results = [r for r in results if r.type == "email"]
        assert len(email_results) == 1
        masked = email_results[0].masked
        assert "***" in masked
        assert "example.com" in masked


class TestBankCardDetection:
    """测试银行卡号检测"""

    def test_detect_bank_card(self):
        """检测银行卡号"""
        protector = PrivacyProtector(level="medium")
        results = protector.detect("卡号6222021234567890123")
        bank_results = [r for r in results if r.type == "bank_card"]
        assert len(bank_results) >= 1

    def test_bank_card_pure_zeros_excluded(self):
        """纯零数字排除"""
        protector = PrivacyProtector(level="medium")
        results = protector.detect("0000000000000000")
        bank_results = [r for r in results if r.type == "bank_card"]
        assert len(bank_results) == 0


class TestPasswordDetection:
    """测试密码检测"""

    def test_detect_password_chinese(self):
        """检测中文密码标记"""
        protector = PrivacyProtector(level="medium")
        results = protector.detect("密码: mySecret123")
        pwd_results = [r for r in results if r.type == "password"]
        assert len(pwd_results) == 1

    def test_detect_password_english(self):
        """检测英文密码标记"""
        protector = PrivacyProtector(level="medium")
        results = protector.detect("password: mySecret123")
        pwd_results = [r for r in results if r.type == "password"]
        assert len(pwd_results) == 1

    def test_detect_password_pwd(self):
        """检测pwd标记"""
        protector = PrivacyProtector(level="medium")
        results = protector.detect("pwd: abc123")
        pwd_results = [r for r in results if r.type == "password"]
        assert len(pwd_results) == 1


class TestIpDetection:
    """测试IP地址检测"""

    def test_detect_ip_address(self):
        """检测IP地址"""
        protector = PrivacyProtector(level="high")
        results = protector.detect("服务器地址192.168.1.100")
        ip_results = [r for r in results if r.type == "ip_address"]
        assert len(ip_results) == 1
        assert ip_results[0].value == "192.168.1.100"

    def test_ip_not_in_medium_level(self):
        """中级别不检测IP"""
        protector = PrivacyProtector(level="medium")
        results = protector.detect("IP是192.168.1.1")
        ip_results = [r for r in results if r.type == "ip_address"]
        assert len(ip_results) == 0

    def test_ip_invalid_octet_excluded(self):
        """无效IP段排除"""
        protector = PrivacyProtector(level="high")
        results = protector.detect("999.999.999.999")
        ip_results = [r for r in results if r.type == "ip_address"]
        assert len(ip_results) == 0

    def test_ip_mask_format(self):
        """IP脱敏格式"""
        protector = PrivacyProtector(level="high")
        results = protector.detect("192.168.1.100")
        ip_results = [r for r in results if r.type == "ip_address"]
        assert len(ip_results) == 1
        masked = ip_results[0].masked
        assert masked.endswith(".***")


class TestMask:
    """测试脱敏功能"""

    def test_mask_phone(self):
        """脱敏手机号"""
        protector = PrivacyProtector(level="medium")
        masked = protector.mask("手机号13812345678")
        assert "138****5678" in masked
        assert "13812345678" not in masked

    def test_mask_id_card(self):
        """脱敏身份证号"""
        protector = PrivacyProtector(level="medium")
        masked = protector.mask("身份证110101199001011234")
        assert "110101199001011234" not in masked
        assert "********" in masked

    def test_mask_preserves_other_text(self):
        """脱敏保留其他文本"""
        protector = PrivacyProtector(level="medium")
        original = "请拨打13812345678联系我"
        masked = protector.mask(original)
        assert "请拨打" in masked
        assert "联系我" in masked

    def test_mask_low_level_no_change(self):
        """低级别不脱敏手机号"""
        protector = PrivacyProtector(level="low")
        text = "手机号13812345678"
        masked = protector.mask(text)
        # low level只检测id_card, bank_card, password，不检测phone
        assert "13812345678" in masked

    def test_mask_no_sensitive_info(self):
        """无敏感信息时原文返回"""
        protector = PrivacyProtector(level="high")
        text = "今天天气真好"
        masked = protector.mask(text)
        assert masked == text

    def test_mask_multiple_sensitive(self):
        """脱敏多处敏感信息"""
        protector = PrivacyProtector(level="medium")
        text = "手机13812345678，身份证110101199001011234"
        masked = protector.mask(text)
        assert "13812345678" not in masked
        assert "110101199001011234" not in masked


class TestCheckAndWarn:
    """测试检查并警告功能"""

    def test_check_and_warn_with_sensitive(self):
        """检测到敏感信息返回True"""
        protector = PrivacyProtector(level="medium")
        has_sensitive, results = protector.check_and_warn("手机13812345678")
        assert has_sensitive is True
        assert len(results) >= 1

    def test_check_and_warn_without_sensitive(self):
        """无敏感信息返回False"""
        protector = PrivacyProtector(level="medium")
        has_sensitive, results = protector.check_and_warn("今天天气真好")
        assert has_sensitive is False
        assert len(results) == 0


class TestSensitiveInfoDataclass:
    """测试SensitiveInfo数据类"""

    def test_sensitive_info_fields(self):
        """SensitiveInfo字段完整性"""
        info = SensitiveInfo(
            type="phone",
            value="13812345678",
            masked="138****5678",
            position=(4, 15),
        )
        assert info.type == "phone"
        assert info.value == "13812345678"
        assert info.masked == "138****5678"
        assert info.position == (4, 15)
