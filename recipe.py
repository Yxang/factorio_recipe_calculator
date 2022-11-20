from dataclasses import dataclass
from typing import Tuple


@dataclass
class Recipe:
    recipe_name: str
    inputs: list[(str, float)]
    outputs: list[(str, float)]
    time: float

    def ser(self):
        return (self.recipe_name,
                ';'.join(['{},{}'.format(inp[0], inp[1]) for inp in self.inputs]),
                ';'.join(['{},{}'.format(out[0], out[1]) for out in self.outputs]),
                self.time
                )

    @staticmethod
    def de(tup: Tuple[str, str, str, float]):
        recipe_name, inputs_str, output_str, time = tup
        inputs = inputs_str.split(';')
        inputs = [(float(inp.split(',')[0]), inp.split(',')[1]) for inp in inputs]

        outputs = output_str.split(';')
        outputs = [(float(out.split(',')[0]), out.split(',')[1]) for out in outputs]
        return Recipe(
            recipe_name=recipe_name,
            inputs=inputs,
            outputs=outputs,
            time=time,
        )


@dataclass
class RecipeInstance:
    recipe: Recipe
    speed: float
    productivity: float
    factory_base_speed: float
