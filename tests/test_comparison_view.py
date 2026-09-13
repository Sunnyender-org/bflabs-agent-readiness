import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('comparison_view', ROOT / 'scripts/render_comparison.py')
view = importlib.util.module_from_spec(spec)
spec.loader.exec_module(view)


class ComparisonViewTests(unittest.TestCase):
    def test_missing_after_and_all_attempts_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p/'experiment.json').write_text(json.dumps({'experiment_id':'exp_a','baseline':{'round_id':'r0'}}))
            row = {'experiment_id':'exp_a','round_id':'r0','platform':'ChatGPT','prompt_id':'q_a','prompt_text':'same question','sample_slot_id':'slot_1','answer_text':'first','attempt_index':1}
            rows = [row,dict(row,answer_text='retry answer',attempt_index=2)]
            (p/'observations.jsonl').write_text('\n'.join(json.dumps(x) for x in rows))
            result = view.render(p,ROOT/'templates/comparison.html')
            self.assertIn('待复测 · 尚无改后回答',result)
            self.assertIn('retry answer',result)
            self.assertEqual(result.count('class="ai-item"'),1)
            rows.append(dict(row,round_id='r1',question_version='2',answer_text='different version'))
            (p/'observations.jsonl').write_text('\n'.join(json.dumps(x) for x in rows))
            self.assertEqual(view.render(p,ROOT/'templates/comparison.html').count('class="ai-item"'),2)

    def test_escape_untrusted_evidence_and_reject_external_local_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            self.assertIsNone(view.local_ref(p,'../secret.png'))
            self.assertIsNone(view.local_ref(p,'https://tracker.example/image.png'))
            row={'answer_text':'<script>alert(1)</script>','cited_urls':['javascript:alert(1)'],'evidence_refs':[]}
            result=view.observation(p,row)
            self.assertNotIn('<script>',result)
            self.assertNotIn('javascript:',result)

    def test_foreign_experiment_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/'experiment.json').write_text('{"experiment_id":"exp_a"}')
            (p/'observations.jsonl').write_text('{"experiment_id":"exp_b"}')
            with self.assertRaises(ValueError):view.render(p,ROOT/'templates/comparison.html')

    def test_starter_nulls_and_literal_template_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            exp=json.loads((ROOT/'templates/round-experiment.json').read_text())
            exp['baseline']=None
            exp['business_window']=None
            (p/'experiment.json').write_text(json.dumps(exp))
            (p/'observations.jsonl').write_text(json.dumps({'round_id':'r0','answer_text':'see {{SOURCES}} and {{BUSINESS}}'}))
            result=view.render(p,ROOT/'templates/comparison.html')
            self.assertIn('已有记录 · 尚未绑定基线',result)
            self.assertIn('see {{SOURCES}} and {{BUSINESS}}',result)
            self.assertIn('待复测',result)
            self.assertIn('未设置',result)

    def test_local_after_is_not_public_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/'actions.json').write_text(json.dumps({'actions':[{'visual_evidence':[{'before':{'environment':'public','viewport':'375x812'},'after':{'environment':'local','viewport':'375x812'}}]}]}))
            result=view.render(p,ROOT/'templates/comparison.html')
            self.assertIn('不能当作线上发布前后验证',result)

    def test_coverage_rows_link_to_page_evidence_and_keep_missing_images(self):
        coverage = {
            "rows": [
                {
                    "question_cluster": "品牌身份",
                    "priority": "P0",
                    "question_ids": ["q_a"],
                    "url": "https://example.com/",
                    "evidence_ref": "screenshots/r0/q_a.png",
                    "disposition": "keep_existing",
                    "status": "planned",
                    "note": "沿用首页。",
                },
                {
                    "question_cluster": "价格蓝图",
                    "priority": "P0",
                    "question_ids": ["q_b"],
                    "url": None,
                    "evidence_ref": None,
                    "disposition": "new_page",
                    "status": "blueprint_ready",
                    "note": "还没有公开页。",
                },
            ]
        }
        questions = {"questions": [{"question_id": "q_a", "text": "What is Example?"}, {"question_id": "q_b", "text": "How much?"}]}
        html = view.coverage_section(coverage, questions)
        self.assertIn("品牌身份", html)
        self.assertIn("What is Example?", html)
        self.assertIn("https://example.com/", html)
        self.assertIn("没有视觉改动", html)
        self.assertIn("公开页还没有", html)
        self.assertNotIn("补造改前画面", html)

    def test_question_plan_does_not_promote_new_candidates(self):
        questions = {"questions":[{"text":"Frozen question", "purpose":"Find official site", "partial_credit_rule":"Check domain"}]}
        backlog = {"next_round_pool":[{"text":"New candidate", "source_kind":"agent_hypothesis", "selection_reason":"Explore next round"}]}
        html = view.question_section(questions, backlog)
        self.assertIn("Frozen question", html)
        self.assertIn("Find official site", html)
        self.assertIn("Check domain", html)
        self.assertIn("下一轮候选问题（1）", html)
        self.assertIn("生成候选，未证明真实需求", html)
        self.assertEqual(questions["questions"][0]["text"], "Frozen question")
