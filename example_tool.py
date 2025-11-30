#!/usr/bin/env python
"""Example toolable CLI tool."""

from toolable import AgentCLI, toolable


@toolable(summary="Add two numbers")
def add(a: int, b: int):
    """Add two numbers and return the sum."""
    return {"sum": a + b}


@toolable(summary="Multiply two numbers")
def multiply(a: int, b: int):
    """Multiply two numbers and return the product."""
    return {"product": a * b}


if __name__ == "__main__":
    cli = AgentCLI("mathtools", tools=[add, multiply], version="1.0.0")
    cli.run()
