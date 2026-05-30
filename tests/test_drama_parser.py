"""Tests for the drama script parser."""


from backend.drama_parser import DialogueLine, parse_line, parse_script


class TestParseLine:
    def test_simple_line(self):
        result = parse_line("小明: 你好啊！")
        assert result == DialogueLine(character="小明", text="你好啊！", emotion=None)

    def test_emotion_line(self):
        result = parse_line("小红: (开心) 很好呀！")
        assert result == DialogueLine(character="小红", text="很好呀！", emotion="开心")

    def test_english_emotion(self):
        result = parse_line("Alice: (happy) Hello!")
        assert result == DialogueLine(character="Alice", text="Hello!", emotion="happy")

    def test_comment_line(self):
        assert parse_line("# this is a comment") is None

    def test_blank_line(self):
        assert parse_line("") is None
        assert parse_line("   ") is None

    def test_no_colon(self):
        assert parse_line("not a valid line") is None

    def test_strips_whitespace(self):
        result = parse_line("  小明 :  你好  ")
        assert result == DialogueLine(character="小明", text="你好", emotion=None)


class TestParseScript:
    def test_basic_script(self):
        script = parse_script(
            "小明: 你好\n小红: 你好呀\n",
            title="Test",
        )
        assert script.title == "Test"
        assert len(script.lines) == 2
        assert script.characters == ["小明", "小红"]

    def test_characters_preserve_order(self):
        script = parse_script(
            "A: one\nB: two\nA: three\nC: four\nA: five\n",
        )
        assert script.characters == ["A", "B", "C"]

    def test_empty_script(self):
        script = parse_script("# only comments\n\n")
        assert script.lines == []
        assert script.characters == []

    def test_mixed_emotions(self):
        script = parse_script(
            "小明: 你好\n小红: (开心) 你好呀\n小明: (思考) 最近怎么样\n",
        )
        assert script.lines[0].emotion is None
        assert script.lines[1].emotion == "开心"
        assert script.lines[2].emotion == "思考"
