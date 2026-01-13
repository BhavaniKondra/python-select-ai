# -----------------------------------------------------------------------------
# Copyright (c) 2025, Oracle and/or its affiliates.
#
# Licensed under the Universal Permissive License v 1.0 as shown at
# http://oss.oracle.com/licenses/upl.
# -----------------------------------------------------------------------------

"""
3200 - Module for testing select_ai agents
"""

import uuid
import logging
import pytest
import select_ai
import os
from select_ai.agent import Agent, AgentAttributes
from select_ai.errors import AgentNotFoundError
import oracledb

# Path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
LOG_FILE = os.path.join(PROJECT_ROOT, "log", "tkex_test_3201_agents.log")
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
# Test constants
# -----------------------------------------------------------------------------

PYSAI_AGENT_NAME = f"PYSAI_3200_AGENT_{uuid.uuid4().hex.upper()}"
PYSAI_AGENT_DESC = "PYSAI_3200_AGENT_DESCRIPTION"
PYSAI_PROFILE_NAME = f"PYSAI_3200_PROFILE_{uuid.uuid4().hex.upper()}"

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def python_gen_ai_profile(profile_attributes):
    logger.info("Creating profile: %s", PYSAI_PROFILE_NAME)
    profile = select_ai.Profile(
        profile_name=PYSAI_PROFILE_NAME,
        description="OCI GENAI Profile",
        attributes=profile_attributes,
    )
    profile.create(replace=True)
    yield profile
    logger.info("Deleting profile: %s", PYSAI_PROFILE_NAME)
    profile.delete(force=True)


@pytest.fixture(scope="module")
def agent_attributes():
    return AgentAttributes(
        profile_name=PYSAI_PROFILE_NAME,
        role="You are an AI Movie Analyst. You analyze movies.",
        enable_human_tool=False,
    )


@pytest.fixture(scope="module")
def agent(python_gen_ai_profile, agent_attributes):
    logger.info("Creating agent: %s", PYSAI_AGENT_NAME)
    agent = Agent(
        agent_name=PYSAI_AGENT_NAME,
        description=PYSAI_AGENT_DESC,
        attributes=agent_attributes,
    )
    agent.create(enabled=True, replace=True)
    yield agent
    logger.info("Deleting agent: %s", PYSAI_AGENT_NAME)
    agent.delete(force=True)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def expect_oracle_error(expected_code, fn):
    """
    Run fn and assert that expected Oracle/Agent error occurs.
    expected_code: "ORA-xxxxx" or "NOT_FOUND"
    """
    try:
        fn()
    except AgentNotFoundError as e:
        logger.info("Expected failure (NOT_FOUND): %s", e)
        assert expected_code == "NOT_FOUND"
    except oracledb.DatabaseError as e:
        msg = str(e)
        logger.info("Expected Oracle failure: %s", msg)
        assert expected_code in msg, f"Expected {expected_code}, got {msg}"
    else:
        pytest.fail(f"Expected error {expected_code} did not occur")

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

def test_3200_identity(agent, agent_attributes):
    logger.info("Verifying agent identity")
    assert agent.agent_name == PYSAI_AGENT_NAME
    assert agent.description == PYSAI_AGENT_DESC
    assert agent.attributes == agent_attributes


@pytest.mark.parametrize("pattern", [None, ".*", "^PYSAI_3200_AGENT_"])
def test_3201_list(pattern):
    logger.info("Listing agents with pattern: %s", pattern)
    if pattern is None:
        agents = list(Agent.list())
    else:
        agents = list(Agent.list(pattern))

    names = [a.agent_name for a in agents]
    logger.info("Agents found: %s", names)
    assert PYSAI_AGENT_NAME in names


def test_3202_fetch(agent_attributes):
    logger.info("Fetching agent: %s", PYSAI_AGENT_NAME)
    a = Agent.fetch(PYSAI_AGENT_NAME)
    assert a.agent_name == PYSAI_AGENT_NAME
    assert a.attributes == agent_attributes
    assert a.description == PYSAI_AGENT_DESC


def test_3203_fetch_non_existing():
    name = f"PYSAI_NO_SUCH_AGENT_{uuid.uuid4().hex}"
    logger.info("Fetching non-existing agent: %s", name)
    expect_oracle_error("NOT_FOUND", lambda: Agent.fetch(name))


def test_3204_disable_enable(agent):
    logger.info("Disabling agent")
    agent.disable()

    logger.info("Enabling agent")
    agent.enable()


def test_3205_set_attribute(agent):
    logger.info("Setting role attribute")
    agent.set_attribute("role", "You are a DB assistant")

    a = Agent.fetch(PYSAI_AGENT_NAME)
    assert "DB assistant" in a.attributes.role


def test_3206_set_attributes(agent):
    logger.info("Replacing attributes")
    new_attrs = AgentAttributes(
        profile_name=PYSAI_PROFILE_NAME,
        role="You are a cloud architect",
        enable_human_tool=True,
    )
    agent.set_attributes(new_attrs)

    a = Agent.fetch(PYSAI_AGENT_NAME)
    assert a.attributes == new_attrs


def test_3207_set_attribute_invalid_key(agent):
    logger.info("Setting invalid attribute key")
    expect_oracle_error("ORA-20050", lambda: agent.set_attribute("no_such_key", 123))

def test_3208_set_attribute_none(agent):
    logger.info("Setting attribute to None")
    expect_oracle_error("ORA-20050", lambda: agent.set_attribute("role", None))

def test_3209_set_attribute_empty(agent):
    logger.info("Setting attribute to empty string")
    expect_oracle_error("ORA-20050", lambda: agent.set_attribute("role", ""))

def test_3210_create_existing_without_replace(agent_attributes):
    logger.info("Create existing agent without replace should fail")
    a = Agent(
        agent_name=PYSAI_AGENT_NAME,
        description="X",
        attributes=agent_attributes,
    )
    expect_oracle_error("ORA-20050", lambda: a.create(replace=False))

def test_3211_delete_and_recreate(agent_attributes):
    name = f"PYSAI_RECREATE_{uuid.uuid4().hex}"
    logger.info("Create agent: %s", name)
    a = Agent(name, attributes=agent_attributes)
    a.create()

    logger.info("Delete agent: %s", name)
    a.delete(force=True)

    logger.info("Recreate agent: %s", name)
    a.create(replace=False)

    logger.info("Cleanup agent: %s", name)
    a.delete(force=True)


def test_3212_disable_after_delete(agent_attributes):
    name = f"PYSAI_TMP_DEL_{uuid.uuid4().hex}"
    a = Agent(name, attributes=agent_attributes)
    a.create()
    a.delete(force=True)
    expect_oracle_error("NOT_FOUND", lambda: a.disable())

def test_3213_enable_after_delete(agent_attributes):
    name = f"PYSAI_TMP_DEL_{uuid.uuid4().hex}"
    a = Agent(name, attributes=agent_attributes)
    a.create()
    a.delete(force=True)
    expect_oracle_error("NOT_FOUND", lambda: a.enable())

def test_3214_set_attribute_after_delete(agent_attributes):
    name = f"PYSAI_TMP_DEL_{uuid.uuid4().hex}"
    a = Agent(name, attributes=agent_attributes)
    a.create()
    a.delete(force=True)
    expect_oracle_error("ORA-20050", lambda: a.set_attribute("role", "X"))


def test_3215_double_delete(agent_attributes):
    name = f"PYSAI_TMP_DOUBLE_DEL_{uuid.uuid4().hex}"
    logger.info("Testing double delete semantics: %s", name)

    a = Agent(name, attributes=agent_attributes)
    a.create()
    a.delete(force=True)

    # As per your Teams learning: force=True allows idempotent delete
    logger.info("Second delete with force=True should succeed")
    a.delete(force=True)


def test_3216_fetch_after_delete(agent_attributes):
    name = f"PYSAI_TMP_FETCH_DEL_{uuid.uuid4().hex}"
    a = Agent(name, attributes=agent_attributes)
    a.create()
    a.delete(force=True)
    expect_oracle_error("NOT_FOUND", lambda: Agent.fetch(name))


def test_3217_list_all_non_empty():
    logger.info("Listing all agents")
    agents = list(Agent.list())
    logger.info("Total agents found: %d", len(agents))
    assert len(agents) > 0

