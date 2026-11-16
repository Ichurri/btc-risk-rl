"""P3 critic objective on one frozen Monte Carlo minibatch."""


def critic_objective(prediction, targets, *, beta: int):
    if type(beta) is not int or beta not in {0, 1}:
        raise ValueError("critic_beta must be 0 or 1")
    if prediction.shape != targets.shape:
        raise ValueError("Critic predictions and targets must have the same shape")
    mse = ((prediction - targets) ** 2).mean()
    if beta == 0:
        # Return the original tensor directly: even a zero addition changes
        # the autograd graph of the control arm.
        return mse, mse, mse.detach().new_zeros(())
    penalty = (prediction**2).mean()
    return mse + penalty, mse, penalty
