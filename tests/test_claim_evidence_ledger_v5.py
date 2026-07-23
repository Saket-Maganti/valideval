from valideval.evidence.ledger import LEDGER_COLUMNS


def test_v5_claim_ledger_contract_has_required_columns() -> None:
    assert LEDGER_COLUMNS == [
        "claim_id",
        "claim_text",
        "claim_category",
        "paper_location",
        "reported_value",
        "verification_status",
        "primary_inputs",
        "reproduction_command",
        "observed_value",
        "tolerance",
        "code_revision",
        "input_hashes",
        "output_hashes",
        "allowed_wording",
        "blocked_wording",
        "notes",
    ]
