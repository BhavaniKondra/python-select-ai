# -----------------------------------------------------------------------------
# Copyright (c) 2025, Oracle and/or its affiliates.
#
# Licensed under the Universal Permissive License v 1.0
# -----------------------------------------------------------------------------

"""
3001 - Complete and backend-aligned test coverage for select_ai.agent Tool APIs
(with logging for behavior visibility)
"""

import uuid
import logging
import pytest
import os
import select_ai
from select_ai.agent import Tool
from select_ai.errors import AgentToolNotFoundError

# Path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
LOG_FILE = os.path.join(PROJECT_ROOT, "log", "tkex_test_3001_tools.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Force logging to file (pytest-proof)
root = logging.getLogger()
root.setLevel(logging.INFO)

for h in root.handlers[:]:
    root.removeHandler(h)

fh = logging.FileHandler(LOG_FILE, mode="w")
fh.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
root.addHandler(fh)

logger = logging.getLogger()

# -----------------------------------------------------------------------------
# Per-test logging
# -----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def log_test_name(request):
    logger.info(f"--- Starting test: {request.function.__name__} ---")
    yield
    logger.info(f"--- Finished test: {request.function.__name__} ---")

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
UUID = uuid.uuid4().hex.upper()

SQL_PROFILE_NAME = f"PYSAI_SQL_PROFILE_{UUID}"
RAG_PROFILE_NAME = f"PYSAI_RAG_PROFILE_{UUID}"

SQL_TOOL_NAME = f"PYSAI_SQL_TOOL_{UUID}"
RAG_TOOL_NAME = f"PYSAI_RAG_TOOL_{UUID}"
PLSQL_TOOL_NAME = f"PYSAI_PLSQL_TOOL_{UUID}"
WEB_SEARCH_TOOL_NAME = f"PYSAI_WEB_TOOL_{UUID}"
PLSQL_FUNCTION_NAME = f"PYSAI_CALC_AGE_{UUID}"

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sql_profile(profile_attributes):
    logger.info("Creating SQL profile: %s", SQL_PROFILE_NAME)
    profile = select_ai.Profile(
        profile_name=SQL_PROFILE_NAME,
        description="SQL Profile",
        attributes=profile_attributes,
    )
    yield profile
    logger.info("Deleting SQL profile")
    profile.delete(force=True)


@pytest.fixture(scope="module")
def rag_profile(rag_profile_attributes):
    logger.info("Creating RAG profile: %s", RAG_PROFILE_NAME)
    profile = select_ai.Profile(
        profile_name=RAG_PROFILE_NAME,
        description="RAG Profile",
        attributes=rag_profile_attributes,
    )
    yield profile
    logger.info("Deleting RAG profile")
    profile.delete(force=True)


@pytest.fixture(scope="module")
def sql_tool(sql_profile):
    logger.info("Creating SQL tool: %s", SQL_TOOL_NAME)
    tool = select_ai.agent.Tool.create_sql_tool(
        tool_name=SQL_TOOL_NAME,
        profile_name=SQL_PROFILE_NAME,
        description="SQL Tool",
        replace=True,
    )
    yield tool
    logger.info("Deleting SQL tool")
    tool.delete(force=True)


@pytest.fixture(scope="module")
def rag_tool(rag_profile):
    logger.info("Creating RAG tool: %s", RAG_TOOL_NAME)
    tool = select_ai.agent.Tool.create_rag_tool(
        tool_name=RAG_TOOL_NAME,
        profile_name=RAG_PROFILE_NAME,
        description="RAG Tool",
        replace=True,
    )
    yield tool
    logger.info("Deleting RAG tool")
    tool.delete(force=True)


@pytest.fixture(scope="module")
def plsql_function():
    logger.info("Creating PL/SQL function: %s", PLSQL_FUNCTION_NAME)
    ddl = f"""
    CREATE OR REPLACE FUNCTION {PLSQL_FUNCTION_NAME}(p_birth_date DATE)
    RETURN NUMBER IS
    BEGIN
        RETURN TRUNC(MONTHS_BETWEEN(SYSDATE, p_birth_date) / 12);
    END;
    """
    with select_ai.cursor() as cur:
        cur.execute(ddl)
    yield
    logger.info("Dropping PL/SQL function")
    with select_ai.cursor() as cur:
        cur.execute(f"DROP FUNCTION {PLSQL_FUNCTION_NAME}")


@pytest.fixture(scope="module")
def plsql_tool(plsql_function):
    logger.info("Creating PL/SQL tool: %s", PLSQL_TOOL_NAME)
    tool = select_ai.agent.Tool.create_pl_sql_tool(
        tool_name=PLSQL_TOOL_NAME,
        function=PLSQL_FUNCTION_NAME,
        description="PL/SQL Tool",
        replace=True,
    )
    yield tool
    logger.info("Deleting PL/SQL tool")
    tool.delete(force=True)

@pytest.fixture(scope="module")
def web_search_tool():
    """Fixture for Web Search Tool positive case."""
    logger.info("Creating Web Search tool: %s", WEB_SEARCH_TOOL_NAME)
    tool = select_ai.agent.Tool.create_websearch_tool(
        tool_name=WEB_SEARCH_TOOL_NAME,
        description="Web Search Tool for testing",
        credential_name="OPENAI_CRED",
        replace=True,
    )
    yield tool
    logger.info("Deleting Web Search tool")
    tool.delete(force=True)

@pytest.fixture(scope="module")
def email_tool():
    logger.info("Creating EMAIL tool: NEG_EMAIL_TOOL")
    tool = select_ai.agent.Tool.create_email_notification_tool(
        tool_name="NEG_EMAIL_TOOL",
        credential_name="EMAIL_CRED",
        recipient="kondra.nagabhavani@oracle.com",
        sender="bharadwaj.vulugundam@oracle.com",
        smtp_host="smtp.email.us-ashburn-1.oci.oraclecloud.com",
        description="Send email",
        replace=True,
    )
    yield tool
    logger.info("Deleting EMAIL tool")
    tool.delete(force=True)

@pytest.fixture(scope="module")
def slack_tool():
    logger.info("Creating SLACK tool: NEG_SLACK_TOOL")
    tool = select_ai.agent.Tool.create_slack_notification_tool(
        tool_name="NEG_SLACK_TOOL",
        credential_name="SLACK_CRED",
        slack_channel="general",
        description="slack notification",
        replace=True,
    )
    yield tool
    logger.info("Deleting SLACK tool")
    tool.delete(force=True)

@pytest.fixture(scope="module")
def http_tool():
    logger.info("Creating HTTP tool: NEG_HTTP_TOOL")
    tool = select_ai.agent.Tool.create_http_tool(
        tool_name="NEG_HTTP_TOOL",
        credential_name="HTTP_CRED",
        endpoint="https://example.com",
        replace=True,
    )
    yield tool
    logger.info("Deleting HTTP tool")
    tool.delete(force=True)

@pytest.fixture(scope="module")
def neg_sql_tool():
    logger.info("Creating SQL tool with INVALID profile: NEG_SQL_TOOL")
    tool = select_ai.agent.Tool.create_sql_tool(
        tool_name="NEG_SQL_TOOL",
        profile_name="NON_EXISTENT_PROFILE",
        replace=True,
    )
    yield tool
    logger.info("Deleting NEG_SQL_TOOL")
    tool.delete(force=True)

@pytest.fixture(scope="module")
def neg_rag_tool():
    logger.info("Creating RAG tool with INVALID profile: NEG_RAG_TOOL")
    tool = select_ai.agent.Tool.create_rag_tool(
        tool_name="NEG_RAG_TOOL",
        profile_name="NON_EXISTENT_RAG_PROFILE",
        replace=True,
    )
    yield tool
    logger.info("Deleting NEG_RAG_TOOL")
    tool.delete(force=True)


@pytest.fixture(scope="module")
def neg_plsql_tool():
    logger.info("Creating PL/SQL tool with INVALID function: NEG_PLSQL_TOOL")
    tool = select_ai.agent.Tool.create_pl_sql_tool(
        tool_name="NEG_PLSQL_TOOL",
        function="NON_EXISTENT_FUNCTION",
        replace=True,
    )
    yield tool
    logger.info("Deleting NEG_PLSQL_TOOL")
    tool.delete(force=True)

# -----------------------------------------------------------------------------
# POSITIVE TESTS
# -----------------------------------------------------------------------------

def test_3000_sql_tool_created(sql_tool):
    logger.info("Validating SQL tool creation")
    assert sql_tool.tool_name == SQL_TOOL_NAME
    assert sql_tool.attributes.tool_params.profile_name == SQL_PROFILE_NAME


def test_3001_rag_tool_created(rag_tool):
    logger.info("Validating RAG tool creation")
    assert rag_tool.tool_name == RAG_TOOL_NAME
    assert rag_tool.attributes.tool_params.profile_name == RAG_PROFILE_NAME


def test_3002_plsql_tool_created(plsql_tool):
    logger.info("Validating PL/SQL tool creation")
    assert plsql_tool.tool_name == PLSQL_TOOL_NAME
    assert plsql_tool.attributes.function == PLSQL_FUNCTION_NAME

def test_3007_web_search_tool_created(web_search_tool):
    logger.info("Validating Web Search tool creation")
    assert web_search_tool.tool_name == WEB_SEARCH_TOOL_NAME

def test_3003_list_tools():
    logger.info("Listing all tools")
    tool_names = {t.tool_name for t in select_ai.agent.Tool.list()}
    logger.info("Tools present: %s", tool_names)

    assert SQL_TOOL_NAME in tool_names
    assert RAG_TOOL_NAME in tool_names
    assert PLSQL_TOOL_NAME in tool_names


def test_3004_list_tools_regex():
    logger.info("Listing tools using regex ^PYSAI_")
    tool_names = {t.tool_name for t in select_ai.agent.Tool.list("^PYSAI_")}
    logger.info("Matched tools: %s", tool_names)

    assert SQL_TOOL_NAME in tool_names
    assert RAG_TOOL_NAME in tool_names
    assert PLSQL_TOOL_NAME in tool_names


def test_3005_fetch_tool():
    logger.info("Fetching SQL tool")
    tool = select_ai.agent.Tool.fetch(SQL_TOOL_NAME)
    assert tool.tool_name == SQL_TOOL_NAME


def test_3006_enable_disable_sql_tool(sql_tool):
    logger.info("Disabling SQL tool")
    sql_tool.disable()
    logger.info("Enabling SQL tool")
    sql_tool.enable()


def test_3008_email_tool_created(email_tool):
    logger.info("Validating EMAIL tool creation")
    assert email_tool.tool_name == "NEG_EMAIL_TOOL"


def test_3009_slack_tool_created(slack_tool):
    logger.info("Validating SLACK tool creation")
    assert slack_tool.tool_name == "NEG_SLACK_TOOL"


def test_3010_http_tool_created(http_tool):
    logger.info("Validating HTTP tool creation")
    assert http_tool.tool_name == "NEG_HTTP_TOOL"

def test_3010_sql_tool_with_invalid_profile_created(neg_sql_tool):
    logger.info("Validating SQL tool with invalid profile is stored")
    assert neg_sql_tool.tool_name == "NEG_SQL_TOOL"
    assert neg_sql_tool.attributes.tool_params.profile_name == "NON_EXISTENT_PROFILE"


def test_3011_rag_tool_with_invalid_profile_created(neg_rag_tool):
    logger.info("Validating RAG tool with invalid profile is stored")
    assert neg_rag_tool.tool_name == "NEG_RAG_TOOL"
    assert neg_rag_tool.attributes.tool_params.profile_name == "NON_EXISTENT_RAG_PROFILE"


def test_3012_plsql_tool_with_invalid_function_created(neg_plsql_tool):
    logger.info("Validating PL/SQL tool with invalid function is stored")
    assert neg_plsql_tool.tool_name == "NEG_PLSQL_TOOL"
    assert neg_plsql_tool.attributes.function == "NON_EXISTENT_FUNCTION"


def test_3017_fetch_non_existent_tool():
    logger.info("Fetching non-existent tool")
    with pytest.raises(AgentToolNotFoundError)as exc:
        select_ai.agent.Tool.fetch("TOOL_DOES_NOT_EXIST")
    logger.error("%s", exc.value)   

def test_3018_list_invalid_regex():
    logger.info("Listing tools with invalid regex")
    with pytest.raises(Exception) as exc:
        list(select_ai.agent.Tool.list(tool_name_pattern="*["))
    logger.error("%s", exc.value)  

def test_3019_list_tools():
    logger.info("Listing all tools")
    tool_names = {t.tool_name for t in select_ai.agent.Tool.list()}
    logger.info("Tools present: %s", tool_names)

    assert SQL_TOOL_NAME in tool_names
    assert RAG_TOOL_NAME in tool_names
    assert PLSQL_TOOL_NAME in tool_names