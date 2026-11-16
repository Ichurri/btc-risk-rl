"""Prospective, source-based evidence marker for completed market optimization."""


def market_training_executed(source_profile, actor_updates, critic_updates):
    """True only after both optimizers ran on accepted training-only source."""
    if any(type(count) is not int or count < 0 for count in (actor_updates, critic_updates)):
        raise ValueError("Invalid completed optimizer counters")
    return (source_profile == "accepted_train_collection_only"
            and actor_updates > 0 and critic_updates > 0)
