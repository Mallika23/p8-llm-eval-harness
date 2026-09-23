"""Providers abstraction: anything that can return a model completion given a prompt and some parameters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Completion:
    """One response from a model, real or replayed."""
    #None=None,optional, defaults to nothing
    text: str
    model_name: str
    latency_ms: float
    token_in: int | None = None
    token_out: int | None = None


class ProviderError(Exception):
    """Base class for anything that goes wrong inside a provider."""

    #ABC + abstractmethod - Provider() on its own raises TypeError, and any subclass that forgets complete() also fails. 
    #It's a contract the language enforces
class Provider(ABC):
    """Abstract base class for a provider of model completions."""
    """A contract every provider must fulfill: given a prompt and some parameters, return a model completion."""

    name: str="base"
    #self is eqv to this name, but this is a more convenient way to access it.
    # * in signature, everything must be passed by name, eg. case_id="case01" just "case01" doesn't work.

    @abstractmethod
    def complete(self,prompt:str,*, case_id:str| None=None)-> Completion:
        """Given a prompt and some parameters, return a model completion."""
        raise NotImplementedError
