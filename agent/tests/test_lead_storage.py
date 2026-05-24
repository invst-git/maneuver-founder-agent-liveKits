import json
import tempfile
import unittest
from pathlib import Path

from src.lead_capture import LeadProfile
from src.lead_store import LeadStore


class LeadProfileTests(unittest.TestCase):
    def test_empty_or_context_only_profile_is_not_persistable(self):
        empty_lead = LeadProfile()
        context_only_lead = LeadProfile()
        context_only_lead.update(problem="Manual intake takes too long")

        self.assertFalse(empty_lead.is_persistable())
        self.assertFalse(context_only_lead.is_persistable())

    def test_contact_company_or_name_with_context_is_persistable(self):
        email_lead = LeadProfile()
        company_lead = LeadProfile()
        named_context_lead = LeadProfile()

        email_lead.update(email="founder@example.com")
        company_lead.update(company="Example Co")
        named_context_lead.update(name="Asha", problem="Manual approvals are slow")

        self.assertTrue(email_lead.is_persistable())
        self.assertTrue(company_lead.is_persistable())
        self.assertTrue(named_context_lead.is_persistable())

    def test_lead_record_excludes_transcript(self):
        lead = LeadProfile()
        lead.update(email="founder@example.com")
        lead.add_transcript_item(role="user", text="Hello")

        record = lead.to_lead_record()

        self.assertIn("email", record)
        self.assertNotIn("transcript", record)

    def test_lead_record_keeps_field_confirmation_statuses(self):
        lead = LeadProfile()
        lead.update(email="founder@example.com")
        lead.set_field_status("email", "confirmed")

        record = lead.to_lead_record()

        self.assertEqual(record["field_statuses"], {"email": "confirmed"})


class LeadStoreTests(unittest.TestCase):
    def test_upsert_keeps_one_record_per_lead_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            leads_file = Path(temp_dir) / "leads.jsonl"
            store = LeadStore(str(leads_file))
            lead = LeadProfile()
            lead.update(email="founder@example.com")

            store.upsert_lead(lead.to_lead_record(), event="capture_lead_info")
            lead.update(company="Example Co")
            store.upsert_lead(lead.to_lead_record(), event="save_lead")

            records = [json.loads(line) for line in leads_file.read_text().splitlines()]

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["lead_id"], lead.lead_id)
            self.assertEqual(records[0]["company"], "Example Co")
            self.assertNotIn("transcript", records[0])

    def test_upsert_keeps_multiple_session_leads(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            leads_file = Path(temp_dir) / "leads.jsonl"
            store = LeadStore(str(leads_file))
            first_lead = LeadProfile()
            second_lead = LeadProfile()

            first_lead.update(email="first@example.com")
            second_lead.update(email="second@example.com")

            store.upsert_lead(first_lead.to_lead_record(), event="save_lead")
            store.upsert_lead(second_lead.to_lead_record(), event="save_lead")

            records = [json.loads(line) for line in leads_file.read_text().splitlines()]

            self.assertEqual(len(records), 2)
            self.assertEqual({record["lead_id"] for record in records}, {first_lead.lead_id, second_lead.lead_id})

    def test_transcript_debug_logging_is_opt_in(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            leads_file = Path(temp_dir) / "leads.jsonl"
            transcripts_file = Path(temp_dir) / "transcripts.jsonl"
            disabled_store = LeadStore(
                str(leads_file),
                transcript_file_path=str(transcripts_file),
                transcript_debug_enabled=False,
            )

            disabled_store.append_transcript_event(
                "lead-1",
                {"timestamp": "now", "role": "user", "text": "Hello", "interrupted": False},
            )

            self.assertFalse(transcripts_file.exists())

            enabled_store = LeadStore(
                str(leads_file),
                transcript_file_path=str(transcripts_file),
                transcript_debug_enabled=True,
            )

            enabled_store.append_transcript_event(
                "lead-1",
                {"timestamp": "now", "role": "user", "text": "Hello", "interrupted": False},
            )

            records = [json.loads(line) for line in transcripts_file.read_text().splitlines()]

            self.assertEqual(records[0]["lead_id"], "lead-1")
            self.assertEqual(records[0]["text"], "Hello")


if __name__ == "__main__":
    unittest.main()
