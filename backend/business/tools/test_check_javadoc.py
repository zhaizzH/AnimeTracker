"""Regression tests for declaration discovery, not business behavior."""
from pathlib import Path
import subprocess
import tempfile
import unittest

TOOL = Path(__file__).with_name("CheckJavadoc.java")


class CheckJavadocTest(unittest.TestCase):
    """Prove that the checker accepts legitimate constructs and rejects known gaps."""

    @classmethod
    def setUpClass(cls):
        cls.compiled = tempfile.TemporaryDirectory()
        subprocess.run(["javac", "-encoding", "UTF-8", "-d", cls.compiled.name, str(TOOL)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.compiled.cleanup()

    def check_source(self, source):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "Sample.java").write_text(source, encoding="utf-8")
            return subprocess.run(["java", "-Dfile.encoding=UTF-8", "-cp",
                                   self.compiled.name, "CheckJavadoc", directory],
                                  encoding="utf-8", capture_output=True)

    def test_chinese_records_private_methods_and_local_variables(self):
        result = self.check_source("""
/**
 * 保存分页序号。
 * @param page 从一开始的页码
 */
record Sample(int page) {
    /**
     * 验证页码是否为正数。
     * @param value 待验证数值
     * @return 正数时返回真
     */
    private boolean positive(int value) {
        int comparison = 0;
        return value > comparison;
    }
}
""")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_natural_javadoc_without_terminal_periods_is_accepted(self):
        result = self.check_source("""
/** 用户会话 */
class Sample {
    /** 会话 ID */
    private final String sessionId;

    /**
     * 读取会话用户
     * @return 用户 ID；不存在时返回 null
     */
    String userId() { return null; }
}
""")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_missing_constructor_and_enum_member_are_reported(self):
        result = self.check_source("""
/** 仅用于枚举声明扫描。 */
enum Sample {
    ONE;
    private Sample() {}
}
""")
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(2, result.stdout.count("missing Javadoc"), result.stdout)

    def test_parameters_and_return_must_match_signature(self):
        result = self.check_source("""
/** 参数检查夹具。 */
class Sample {
    /**
     * 读取输入值。
     * @param stale 已更名的参数
     */
    int read(int value) { return value; }
}
""")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("@param expected=[value] actual=[stale]", result.stdout)
        self.assertIn("@return count=0", result.stdout)

    def test_override_can_inherit_but_constructor_cannot(self):
        accepted = self.check_source("""
/** 覆盖方法继承标准库契约。 */
class Sample {
    /** {@inheritDoc} */
    @Override public String toString() { return "sample"; }
}
""")
        self.assertEqual(0, accepted.returncode, accepted.stdout)
        rejected = self.check_source("""
/** 构造器继承的错误夹具。 */
class Sample {
    /** {@inheritDoc} */
    private Sample() {}
}
""")
        self.assertNotEqual(0, rejected.returncode)
        self.assertIn("inheritDoc requires", rejected.stdout)

    def test_template_summary_is_rejected(self):
        result = self.check_source("""
/** 验证对应组件在该场景下保持既定契约。 */
class Sample {}
""")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("mechanical summary", result.stdout)

    def test_malformed_java_and_inline_tag_fail(self):
        for source in (
            "/** 无效声明。 */ class Sample { " + chr(92) + "r" + chr(92) + "n }",
            "/** 文档中的未闭合链接 {@link String */ class Sample {}",
        ):
            with self.subTest(source=source):
                result = self.check_source(source)
                self.assertNotEqual(0, result.returncode, result.stdout)


if __name__ == "__main__":
    unittest.main()
