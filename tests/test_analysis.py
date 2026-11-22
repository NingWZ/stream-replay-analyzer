import unittest

from analysis_core import Comment, candidates, parse_chat, playback_start


class ReplayTests(unittest.TestCase):
    def test_seek(self):
        for second, expected in [(0, 0), (2, 0), (5, 0), (12, 7)]:
            with self.subTest(second=second):
                self.assertEqual(playback_start(second), expected)

    def test_empty_log(self):
        comments = parse_chat(b"seconds,message\r\n", 30)
        self.assertEqual(comments, [])
        self.assertEqual(candidates(comments, 30), [])

    def test_adjacent_peaks_and_gap(self):
        rows = [Comment(s, str(s)) for s in [4, 4, 4, 5, 6, 7, 8, 10, 12, 15, 15, 16]]
        result = candidates(rows[::-1], 16.5)
        self.assertEqual([(r.start, r.end, r.count, r.windows) for r in result],
                         [(0, 10, 7, 2), (15, 16.5, 3, 1)])
        self.assertEqual(result[0].representative, Comment(5, "5"))

    def test_multilingual_bom_stable_order(self):
        data = 'seconds,message\r\n9,日本語\r\n2,"中文,来了"\r\n9,次です'
        self.assertEqual(parse_chat(data.encode("utf-8-sig"), 10),
                         [Comment(2, "中文,来了"), Comment(9, "日本語"), Comment(9, "次です")])

    def test_invalid_csv(self):
        for data, hint in [(b"", "1 行目"), (b"seconds,text", "1 行目"), (b"\xff", "UTF-8"),
                           (b"seconds,message\n1, ", "2 行目"), (b"seconds,message\n1,a,b", "2 行目"),
                           (b"seconds,message\n-1,a", "2 行目"), (b"seconds,message\n30,a", "範囲外"),
                           (b'seconds,message\n1,"abc', "引用符")]:
            with self.subTest(data=data):
                with self.assertRaisesRegex(ValueError, hint):
                    parse_chat(data, 30)

