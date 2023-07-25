# pyright: strict, reportUntypedFunctionDecorator=false
import os

from invoke.context import Context
from invoke.tasks import task  # pyright: ignore [reportUnknownVariableType]

use_pty = not os.getenv("CI", "")


@task(optional=["args"], help={"args": "pytest additional arguments"})
def test(ctx: Context, args: str | None = ""):
    """run tests (without coverage)"""
    ctx.run(f"pytest {args}", pty=use_pty)


@task(optional=["args"], help={"args": "pytest additional arguments"})
def test_cov(ctx: Context, args: str | None = ""):
    """run test vith coverage"""
    ctx.run(f"coverage run -m pytest {args}", pty=use_pty)


@task()
def report_cov(ctx: Context):
    """report coverage"""
    ctx.run("coverage combine", warn=True, pty=use_pty)
    ctx.run("coverage report --show-missing", pty=use_pty)


@task(optional=["args"], help={"args": "pytest additional arguments"})
def coverage(ctx: Context, args: str | None = ""):
    """run tests and report coverage"""
    test_cov(ctx, args)
    report_cov(ctx)


@task(
    optional=["args"], help={"args": "linting tools (black, ruff) additional arguments"}
)
def lint_black(ctx: Context, args: str | None = ""):
    args = args or "."
    ctx.run("black --version", pty=use_pty)
    ctx.run(f"black --check --diff {args}", pty=use_pty)


@task(
    optional=["args"], help={"args": "linting tools (black, ruff) additional arguments"}
)
def lint_ruff(ctx: Context, args: str | None = ""):
    args = args or "."
    ctx.run("ruff --version", pty=use_pty)
    ctx.run(f"ruff check {args}", pty=use_pty)


@task(
    optional=["args"], help={"args": "linting tools (black, ruff) additional arguments"}
)
def lintall(ctx: Context, args: str | None = ""):
    """check linting"""
    args = args or "."
    lint_black(ctx, args)
    lint_ruff(ctx, args)


@task(optional=["args"], help={"args": "check tools (pyright) additional arguments"})
def check_pyright(ctx: Context, args: str | None = ""):
    """check static types with pyright"""
    args = args or ""
    ctx.run("pyright --version")
    ctx.run(f"pyright {args}", pty=use_pty)


@task(optional=["args"], help={"args": "check tools (pyright) additional arguments"})
def checkall(ctx: Context, args: str | None = ""):
    """check static types"""
    args = args or ""
    check_pyright(ctx, args)


@task(optional=["args"], help={"args": "black additional arguments"})
def fix_black(ctx: Context, args: str | None = ""):
    """fix black formatting"""
    args = args or "."
    ctx.run(f"black {args}", pty=use_pty)  # type: ignore


@task(optional=["args"], help={"args": "ruff additional arguments"})
def fix_ruff(ctx: Context, args: str | None = ""):
    """fix all ruff rules"""
    args = args or "."
    ctx.run(f"ruff --fix {args}", pty=use_pty)  # type: ignore


@task(
    optional=["args"],
    help={"args": "linting (fix mode) tools (black, ruff) additional arguments"},
)
def fixall(ctx: Context, args: str | None = ""):
    """fix everything automatically"""
    args = args or "."
    fix_black(ctx, args)
    fix_ruff(ctx, args)
    lintall(ctx, args)
