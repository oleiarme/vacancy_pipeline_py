from vacancy_pipeline_py.cli import dual_run_diff, gmail_auth, orchestrate, send_telegram, sync_supabase, verify


def test_cli_modules_expose_main_functions():
    assert callable(dual_run_diff.main)
    assert callable(gmail_auth.main)
    assert callable(orchestrate.main)
    assert callable(send_telegram.main)
    assert callable(sync_supabase.main)
    assert callable(verify.main)
