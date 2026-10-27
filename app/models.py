from sqlalchemy import Column, Date, Float, Integer, String, Text

from app.db import Base


class Offering(Base):
    """One priced thing you can buy: an LLM model, a grounding surcharge, a
    SERP API, a subscription seat, a discount.

    Deliberately one flat table rather than a model/vendor/price hierarchy.
    The catalog is read-mostly reference data, the shapes vary a lot between
    an LLM's four token prices and a SERP API's single per-1000 rate, and a
    flat table keeps both the JSON seed file and the UI filters obvious.
    """

    __tablename__ = "offerings"

    id = Column(Integer, primary_key=True)

    provider = Column(String(80), nullable=False, index=True)
    name = Column(String(160), nullable=False)
    model_id = Column(String(120), nullable=True)
    kind = Column(String(32), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="current", index=True)

    context_window = Column(Integer, nullable=True)
    max_output = Column(Integer, nullable=True)

    # Per-million-token prices, for kind == "llm_model".
    price_input = Column(Float, nullable=True)
    price_output = Column(Float, nullable=True)
    price_cache_write_5m = Column(Float, nullable=True)
    price_cache_write_1h = Column(Float, nullable=True)
    price_cache_read = Column(Float, nullable=True)

    # Everything that isn't priced per token: per 1,000 requests, per month,
    # per hour, percent off. unit_label carries the unit in words.
    unit_price = Column(Float, nullable=True)
    unit_label = Column(String(80), nullable=True)

    free_tier = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Provenance. Non-negotiable per row: a price with no source and no date
    # is not usable in a client quote.
    confidence = Column(String(16), nullable=False, default="unverified", index=True)
    source_url = Column(Text, nullable=True)
    as_of = Column(Date, nullable=True)

    @property
    def is_token_priced(self):
        return self.price_input is not None or self.price_output is not None

    def blended_cost(self, tokens_in, tokens_out):
        """USD for a given token mix. Used only for sorting token-priced rows
        by a like-for-like figure, since input and output prices move apart."""
        if not self.is_token_priced:
            return None
        pin = self.price_input or 0.0
        pout = self.price_output or 0.0
        return (tokens_in / 1_000_000.0) * pin + (tokens_out / 1_000_000.0) * pout
