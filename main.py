"""
Zoo is a game about what happens when the humans disappear and the animals take over.
The game is an overhead view of a zoo, where the player is given the role of one of the animals.
The goal is to survive as long as possible, and to do so the player must eat, sleep, and reproduce.
The player can also interact with other animals, and the player can also interact with the environment.
The player can be a carnivore, herbivore, or omnivore, and the player can be a predator or prey since
it's random what animal the player is.
"""

import itertools
import random


class LifeException(Exception):
    def __init__(self, animal):
        self.animal = animal

    def __str__(self):
        return f"{self.__str__} has died"


class Animal:
    """
    This is the base class for all animals.
    """

    def __init__(self):
        """
        This method is called when the animal is created.
        """
        self.strength = 1
        self.speed = 1
        self.size = 1
        self.hunger = 1
        self.thirst = 1
        self.energy = 1
        self.virility = 1
        self.age = 1
        self.favorite_food = None
        self.position = [0, 0]
        self.motive = "mate"
        self.nutrition = 1
        self.gender = random.choice(["male", "female"])
        self.safe_spot = []
        self.animals_nearby = []
        self.nearby_unoccupied_tiles = []
        self.nearby_occupied_tiles = []

    def check_nearby_tiles(self, grid):
        self.nearby_unoccupied_tiles = [
            [self.position[0] + row, self.position[1] + col]
            for row, col in itertools.product(range(-1, 2), range(-1, 2))
            if grid[self.position[0] + row][self.position[1] + col] is None
        ]
        self.nearby_occupied_tiles = [
            {grid[self.position[0] + row][self.position[1] + col]}
            for row, col in itertools.product(
                range(-self.speed, self.speed + 1),
                range(-self.speed, self.speed + 1),
            )
            if grid[self.position[0] + row][self.position[1] + col] is not None
        ]

    def check_nearby_animals(self, grid):
        self.check_nearby_tiles(grid)
        self.animals_nearby = [
            animal
            for animal in self.nearby_occupied_tiles
            if isinstance(animal, Animal)
        ]

    def drink(self, water, zoo):
        """
        This method is called when the animal drinks.
        """
        if water.size > 1:
            water.size -= 1
            self.thirst -= 1
            self.energy += 1
        else:
            self.thirst += 1
            self.energy -= 1
            zoo.remove_water(water)

    def sleep(self):
        """
        This method is called when the animal sleeps.
        """

        self.energy += 1

    def mate(self, partner):
        """
        This method is called when the animal mates.
        """
        if partner.virility > 0:
            self.virility -= 1
            self.energy += 1
        # return a new animal of the same type
        return self.__class__()

    def grow(self):
        """
        This method is called when the animal grows.
        """

        self.strength += 1
        self.speed += 1
        self.size += 1
        self.hunger += 1
        self.thirst += 1
        self.energy += 1
        self.virility += 1
        self.age += 1

    def die(self):
        """
        This method is called when the animal dies.
        """

        self.strength = 0
        self.speed = 0
        self.size = 0
        self.hunger = 0
        self.thirst = 0
        self.energy = 0
        self.virility = 0
        self.age = "Dead"

    def __str__(self):
        """
        This method is called when the animal is printed.
        """

        return "Animal"

    def attack(self, opponent, modifier=0, special_attack=1):
        """
        This method is called when the animal attacks. Roll a d20 and add the strength to the roll.
        """
        attack_modifier = self.strength + modifier
        if isinstance(opponent, self.favorite_food):
            attack_modifier += special_attack

        return random.randint(1, 20) + attack_modifier

    def defend(self, opponent, modifier=0, special_defense=1):
        """
        This method is called when the animal defends. Roll a d20 and add the speed to the roll.
        """
        defense_modifier = self.speed + modifier
        if isinstance(opponent, self.favorite_food):
            defense_modifier += special_defense
        return random.randint(1, 20) + defense_modifier

    def move(self, direction):
        """
        This method is called when the animal moves. The direction is a list of two numbers.
        """
        self.position[0] += direction[0]
        self.position[1] += direction[1]

    def motivation(self):
        """
        This determines what the animals most urgent need is i.e. eat, sleep, drink, mate, etc.
        """
        if self.energy == 0:
            raise LifeException(self)

        needs = {
            "drink": self.thirst,
            "eat": self.hunger,
            "sleep": self.energy,
            "mate": self.virility,
        }
        self.motive = min(needs, key=needs.get)
        print(f"{self} is motivated by {self.motive}")

    def turn(self, grid, zoo):
        """
        This method is called when the animal takes a turn.
        """
        self.safe_spot = self.look_for_safe_spot(grid)
        self.motivation()
        self.base_hunger(grid)
        self.base_thirst(grid)
        self.base_rest(grid)
        self.base_reproduce(grid, zoo)

    def base_reproduce(self, grid, zoo):
        if self.motive == "mate" and (found_partner := self.look_for_partner(grid)):
            baby = self.mate(found_partner)
            # add baby to zoo and move it to an adjacent empty spot
            empty_spots = [
                [self.position[0] + i, self.position[1] + j]
                for i, j in itertools.product(range(-1, 2), range(-1, 2))
                if isinstance(
                    grid[self.position[0] + i][self.position[1] + j], type(None)
                )
            ]
            baby.position = random.choice(empty_spots)
            zoo.append(baby)
        else:
            # move towards random direction
            self.move([random.randint(-1, 1), random.randint(-1, 1)])

    def base_rest(self, grid):
        if self.motive == "sleep":
            if safe_spot := self.look_for_safe_spot(grid):
                self.move(safe_spot)
                self.sleep()
            self.sleep()

    def base_thirst(self, grid):
        if self.motive == "drink":
            if found_water := self.look_for_water(grid):
                self.move(found_water)
                self.drink()
            else:
                # move towards random direction
                self.move([random.randint(-1, 1), random.randint(-1, 1)])

    def base_hunger(self, grid, func=None):
        if func is None:
            func = self.look_for_food
        if self.motive == "eat":
            if found_food := func(grid):
                self.move(found_food)
                self.eat(found_food)
            else:
                # move towards random direction
                self.move([random.randint(-1, 1), random.randint(-1, 1)])

    def look_for_food(self, grid):
        """
        This method is called when the animal looks for food in the reach of the animals speed.
        """
        if nearby_food := [
            grid[self.position[0] + i][self.position[1] + j]
            for i, j in itertools.product(
                range(-self.speed, self.speed + 1),
                range(-self.speed, self.speed + 1),
            )
            if isinstance(
                grid[self.position[0] + i][self.position[1] + j],
                self.favorite_food,
            )
        ]:
            return min(nearby_food, key=lambda x: x.size)
        return None

    def look_for_partner(self, grid):
        """
        This method is called when the animal looks for a partner of the same species and opposite sex.
        """

        if self.safe_spot:
            if compatible_partners := [
                partner for partner in nearby_partners if partner.sex != self.sex
            ]:
                return (
                    random.choice(partners_in_safe_spots)
                    if (
                        partners_in_safe_spots := [
                            partner
                            for partner in compatible_partners
                            if self.look_for_safe_spot(grid) == partner.position
                        ]
                    )
                    else random.choice(compatible_partners)
                )
        return None

    def look_for_water(self, grid):
        """
        This method is called when the animal looks for water in the reach of the animals speed.
        """
        if nearby_water := [
            grid[self.position[0] + i][self.position[1] + j]
            for i, j in itertools.product(
                range(-self.speed, self.speed + 1),
                range(-self.speed, self.speed + 1),
            )
            if isinstance(grid[self.position[0] + i][self.position[1] + j], Water)
        ]:
            return min(nearby_water, key=lambda x: x.size)
        return None

    def look_for_safe_spot(self, grid):
        """
        This method is called when the animal looks for a safe spot to mate or sleep.
        A safe spot is a spot where no other animal of the same species is present.
        """

        if nearby_safe_spot := [
            grid[self.position[0] + i][self.position[1] + j]
            for i, j in itertools.product(
                range(-self.speed, self.speed + 1),
                range(-self.speed, self.speed + 1),
            )
            if isinstance(
                grid[self.position[0] + i][self.position[1] + j], self.__class__
            )
        ]:
            return min(nearby_safe_spot, key=lambda x: x.size)

        return None

    def eat(self, grid, zoo):
        """
        If an Animal is adjacent to a compatible food it will eat it.
        """
        # compatible foods are either plants or animals or both. We can derive that by seeing the
        # base class of the favorite food.
        compatible_food_class = Plant
        if isinstance(self.favorite_food, Animal):
            compatible_food_class = DeadAnimal

        for i, j in itertools.product(range(-1, 2), range(-1, 2)):
            if isinstance(
                grid[self.position[0] + i][self.position[1] + j], compatible_food_class
            ):
                self.hunger -= grid[self.position[0] + i][
                    self.position[1] + j
                ].nutrition
                grid[self.position[0] + i][self.position[1] + j] = None
                self.grow()
            else:
                attack = self.attack(compatible_food_class)
                defense = compatible_food_class.defend()
                if attack > defense:
                    compatible_food_class.energy -= attack - defense
                    if compatible_food_class.energy <= 0:
                        # the food is dead now, replace it with a dead animal
                        zoo.remove_animal(compatible_food_class)


class Carnivore(Animal):
    """
    This is the class for carnivores.
    """

    def __init__(self):
        """
        This method is called when the carnivore is created.
        """
        self.favorite_food = Animal
        super().__init__()

    def __str__(self):
        """
        This method is called when the carnivore is printed.
        """

        return "Carnivore"


class Herbivore(Animal):
    """
    This is the class for herbivores.
    """

    def __init__(self):
        """
        This method is called when the herbivore is created.
        """
        self.favorite_food = Plant
        super().__init__()

    def __str__(self):
        """
        This method is called when the herbivore is printed.
        """

        return "Herbivore"


class Omnivore(Animal):
    """
    This is the class for omnivores.
    """

    def __init__(self):
        """
        This method is called when the omnivore is created.
        """
        self.favorite_food = Plant
        super().__init__()

    def __str__(self):
        """
        This method is called when the omnivore is printed.
        """

        return "Omnivore"


class Predator(Carnivore):
    """
    This is the class for predators.
    """

    def __init__(self):
        """
        This method is called when the predator is created.
        """
        self.favorite_food = Prey
        super().__init__()

    def __str__(self):
        """
        This method is called when the predator is printed.
        """

        return "Predator"

    def turn(self, grid, zoo):
        """
        This method is called when the animal takes a turn.
        """
        self.motivation()
        self.predator_hunger(grid)
        self.base_thirst(grid)
        self.base_rest(grid)
        self.base_reproduce(grid, zoo)
        self.motivation()

    def predator_hunger(self, grid):
        if self.motive == "hunger":
            if found_food := self.hunt(grid):
                self.move(found_food)
                self.eat(found_food)
            else:
                # move towards random direction
                self.move([random.randint(-1, 1), random.randint(-1, 1)])

    def hunt(self, grid):
        """
        This method is called when the predator hunts.
        The predator will check the surrounding tiles for prey and move towards it.
        The predator can move its speed in any direction and will attack the prey if it is in range.
        """
        self.check_nearby_animals(grid)

        for animal in self.animals_nearby:
            if isinstance(animal, self.favorite_food) or not isinstance(
                animal, self.__class__
            ):
                # the predator will change its position to an unoccupied tile adjacent to the prey
                self.check_nearby_tiles(grid)
                self.position = random.choice(self.nearby_unoccupied_tiles)


class Prey(Herbivore):
    """
    This is the class for prey.
    """

    def __init__(self):
        """
        This method is called when the prey is created.
        """
        self.favorite_food = Plant
        super().__init__()

    def __str__(self):
        """
        This method is called when the prey is printed.
        """

        return "Prey"

    def run_away(self, grid):
        """
        If the prey is near a predator, it will run away.
        """
        self.check_nearby_animals(grid)

        try:
            nearest_predator = min(
                self.animals_nearby, key=lambda x: abs(x.position[0] - self.position[0])
            )
        except ValueError:
            nearest_predator = None
        if nearest_predator and isinstance(nearest_predator, Predator):
            # the prey will change its position to an unoccupied tile adjacent to the predator
            self.check_nearby_tiles(grid)
            self.position = random.choice(self.nearby_unoccupied_tiles)

    def turn(self, grid, zoo):
        """
        This method is called when the animal takes a turn.
        """
        self.run_away(grid)
        self.motivation()
        self.base_hunger(grid)
        self.base_thirst(grid)
        self.base_rest(grid)
        self.base_reproduce(grid, zoo)


class Zoo:
    """
    This is the class for the zoo.
    """

    def __init__(self, height, width):
        """
        This method is called when the zoo is created.
        """
        self.animals = []
        self.plants = []
        self.water_sources = []
        self.height = height
        self.width = width
        # grid is a matrix of the same size as the zoo
        # it contains the string representation of the animal at that position
        self.grid = [[None for _ in range(width)] for _ in range(height)]

    def add_animal(self, animal):
        """
        This method is called when an animal is added to the zoo.
        """
        # place the animal in the grid
        self.grid[animal.position[0]][animal.position[1]] = animal.__str__()
        self.animals.append(animal)

    def remove_animal(self, animal):
        """
        This method is called when an animal is removed from the zoo.
        """
        # remove the animal from the grid
        self.grid[animal.position[0]][animal.position[1]] = None
        self.animals.remove(animal)
        # replace the animal with a DeadAnimal
        self.add_animal(DeadAnimal(animal))

    def __str__(self):
        """
        This method is called when the zoo is printed.
        """

        return "Zoo"

    def add_plant(self, plant):
        """
        This method is called when a plant is added to the zoo.
        """
        # place the plant in the grid
        self.grid[plant.position[0]][plant.position[1]] = plant.__str__()
        self.plants.append(plant)

    def remove_plant(self, plant):
        """
        This method is called when a plant is removed from the zoo.
        """
        # remove the plant from the grid
        self.grid[plant.position[0]][plant.position[1]] = None
        self.plants.remove(plant)

    def remove_water(self, water):
        """
        This method is called when water is removed from the zoo.
        """
        # remove the water from the grid
        self.grid[water.position[0]][water.position[1]] = None
        self.water_sources.remove(water)

    def add_water(self, water):
        """
        This method is called when water is added to the zoo.
        """
        # place the water in the grid
        self.grid[water.position[0]][water.position[1]] = water.__str__()
        self.water_sources.append(water)

    def print_grid(self):
        """
        This method is called when the grid is printed.
        """
        print(self.grid)


class Scavenger(Animal):
    """
    This is the class for scavengers.
    """

    def __init__(self):
        """
        This method is called when the scavenger is created.
        """
        self.favorite_food = DeadAnimal
        super().__init__()

    def __str__(self):
        """
        This method is called when the scavenger is printed.
        """

        return "Scavenger"

    def scavenge(self, grid):
        """
        This method is called when the scavenger scavenges.
        """
        self.check_nearby_tiles(grid)
        nearest_dead_animal = min(
            self.nearby_occupied_tiles,
            key=lambda x: abs(x.position[0] - self.position[0]),
        )
        if isinstance(nearest_dead_animal, DeadAnimal):
            # the scavenger will change its position to an unoccupied tile adjacent to the dead animal
            self.check_nearby_tiles(grid)
            self.position = random.choice(self.nearby_unoccupied_tiles)

    def turn(self, grid, zoo):
        """
        This method is called when the animal takes a turn.
        """
        self.motivation()
        self.base_hunger(grid, func=self.scavenge)
        self.base_thirst(grid)
        self.base_rest(grid)
        self.base_reproduce(grid, zoo)


class Plant:
    """
    This is the class for plants.
    """

    def __init__(self):
        """
        This method is called when the plant is created.
        """
        self.size = 1
        self.age = 1
        self.nutrients = 1
        self.favorite_food = DeadAnimal
        self.position = [random.randint(0, 9), random.randint(0, 9)]

    def grow(self):
        """
        This method is called when the plant grows.
        """

        self.size += 1
        self.age += 1

    def die(self):
        """
        This method is called when the plant dies.
        """

        self.size = 0
        self.age = "Dead"

    def __str__(self):
        """
        This method is called when the plant is printed.
        """

        return "Plant"

    def turn(self, grid, zoo):
        """
        On a plants turn it will grow and then check if it can reproduce.
        """
        self.grow()
        self.reproduce(grid, zoo)

    def reproduce(self, grid, zoo):
        """
        A plant will reproduce if it is near an empty tile or another plant or water.
        """
        self.check_nearby_tiles(grid)
        if self.unoccupied_tiles:
            baby_plant = self.__class__()
            baby_plant.position = random.choice(empty_tiles)
            zoo.add_plant(baby_plant)
            return
        # check if the nearby tiles are occupied by a plant
        if self.nearby_occupied_tiles and all(
            isinstance(plant, Plant) for plant in self.nearby_occupied_tiles
        ):
            baby_plant = self.__class__()
            baby_plant.position = random.choice(empty_tiles)
            zoo.add_plant(baby)


class Tree(Plant):
    """
    This is the class for trees.
    """

    def __init__(self):
        """
        This method is called when the tree is created.
        """
        super().__init__()

    def __str__(self):
        """
        This method is called when the tree is printed.
        """

        return "Tree"


class Bush(Plant):
    """
    This is the class for bushes.
    """

    def __init__(self):
        """
        This method is called when the bush is created.
        """
        super().__init__()

    def __str__(self):
        """
        This method is called when the bush is printed.
        """

        return "Bush"


class Grass(Plant):
    """
    This is the class for grass.
    """

    def __init__(self):
        """
        This method is called when the grass is created.
        """
        super().__init__()

    def __str__(self):
        """
        This method is called when the grass is printed.
        """

        return "Grass"


class DeadAnimal:
    """
    This is the class for dead animals.
    """

    def __init__(self, former_animal=None):
        """
        This method is called when the dead animal is created.
        """
        self.former_animal = former_animal.__str__()
        self.nutrients = former_animal.size + former_animal.vitality
        self.size = former_animal.size
        self.position = former_animal.position

    def decompose(self):
        """
        This method is called when the dead animal decomposes.
        """

        self.size -= 1
        self.nutrients -= 1
        self.age += 1


class Lion(Predator):
    """
    This is the class for lions.
    """

    def __init__(self):
        """
        This method is called when the lion is created.
        """
        self.strength = 5
        self.size = 5
        self.favorite_food = Zebra
        super().__init__()

    def __str__(self):
        """
        This method is called when the lion is printed.
        """

        return "Lion"


class Zebra(Prey):
    """
    This is the class for zebras.
    """

    def __init__(self):
        """
        This method is called when the zebra is created.
        """
        self.favorite_food = Grass
        self.speed = 5
        self.size = 3
        super().__init__()

    def __str__(self):
        """
        This method is called when the zebra is printed.
        """

        return "Zebra"


class Elephant(Herbivore):
    """
    This is the class for elephants.
    """

    def __init__(self):
        """
        This method is called when the elephant is created.
        """
        self.strength = 10
        self.size = 10
        self.favorite_food = Tree
        super().__init__()

    def __str__(self):
        """
        This method is called when the elephant is printed.
        """

        return "Elephant"


class Hyena(Scavenger):
    """
    This is the class for hyenas.
    """

    def __init__(self):
        """
        This method is called when the hyena is created.
        """
        self.strength = 3
        self.size = 3
        self.favorite_food = DeadAnimal
        super().__init__()

    def __str__(self):
        """
        This method is called when the hyena is printed.
        """

        return "Hyena"


class Giraffe(Prey):
    """
    This is the class for giraffes.
    """

    def __init__(self):
        """
        This method is called when the giraffe is created.
        """
        self.favorite_food = Tree
        self.speed = 3
        self.size = 5
        super().__init__()

    def __str__(self):
        """
        This method is called when the giraffe is printed.
        """

        return "Giraffe"


class Rhino(Herbivore):
    """
    This is the class for rhinos.
    """

    def __init__(self):
        """
        This method is called when the rhino is created.
        """
        self.strength = 7
        self.size = 7
        self.favorite_food = Bush
        super().__init__()

    def __str__(self):
        """
        This method is called when the rhino is printed.
        """

        return "Rhino"


class Water:
    """
    This is the class for water on the map.
    """

    def __init__(self):
        """
        This method is called when the water is created.
        """
        self.position = [0, 0]
        self.size = random.randint(1, 1000)


def create_zoo():
    """
    This function creates the zoo.
    """

    zoo = Zoo(height=100, width=100)

    # fill the zoo with random animals
    empty_grid_tiles = 1000
    for row, column in itertools.product(range(100), range(100)):
        selection = random.choice(["animal", "plant", "water"])
        if selection == "animal":
            if empty_grid_tiles > 0:
                empty_grid_tiles -= 1
                animal = random.choice([Lion, Zebra, Elephant, Hyena, Giraffe, Rhino])
                animal = animal()
                animal.position = [row, column]
                zoo.add_animal(animal)
                zoo.grid[row][column] = animal
        elif selection == "plant":
            if empty_grid_tiles > 0:
                empty_grid_tiles -= 1
                plant = random.choice([Tree, Bush, Grass])
                plant = plant()
                plant.position = [row, column]
                zoo.add_plant(plant)
                zoo.grid[row][column] = plant
        elif selection == "water":
            if empty_grid_tiles > 0:
                empty_grid_tiles -= 1
                water = Water()
                water.position = [row, column]
                zoo.add_water(water)
                zoo.grid[row][column] = water

    return zoo


def main():
    """
    This function is the main function.
    """

    # create the zoo
    zoo = create_zoo()
    zoo.print_grid() # this grid should be 2d but it's only 1d and the second dimension is a lst of Nones
    # print the zoo

    animals = True
    turn = 1
    while animals:
        # run the simulation
        print(f"Turn {turn}")

        for animal in zoo.animals:
            print(f"{animal} is at {animal.position}")
            animal.turn(zoo.grid, zoo)
        turn += 1


# run the simulation
main()
