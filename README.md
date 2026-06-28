# The Revenge Cycle

Submission for the [Very Serious Juniper Game Dev Jam](https://itch.io/jam/theveryseriousjuniperdevgamejam), theme was 'spin the wheel'. You play as two chefs with a vendetta, who wreck each other's restaurants using randomly selected weapons, continuing the 'cycle' until one dies.

## Running

Make sure you have python and pip installed beforehand.

```
# get source code:
git clone --depth 1 https://github.com/anqelinthestarsxx/The-Revenge-Cycle.git
cd The-Revenge-Cycle

# install dependencies (NOTE: pygame-ce not pygame)
pip install pygame-ce moderngl

# run it!
python main.py
```

If you already have pygame installed, you may need to remove it and install pygame-ce instead as such: `pip uninstall pygame`, then `pip install pygame-ce`.
