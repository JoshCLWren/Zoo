import contextlib
import itertools
import random

from environment.liquids import Water
from organisms.dead_things import Corpse
from organisms.organisms import LifeException, Organism
from organisms.plants import Bush, Grass, Plant, Tree
import logging

class Animal(Organism):
    """
    This is the base class for all animals.
    """

    def __init__(self):
        """
        This method is called when the animal is created.
        """
        super().__init__()
        self.sleep_counter = 0
        self.strength = 1
        self.speed = 1
        self.size = 1
        self.hunger = 50
        self.thirst = 50
        self.energy = 50
        self.virility = 50
        self.age = 1
        self.favorite_food = None
        self.position: list = [0, 0]
        self.motive = "mate"
        self.nutrients = 1
        self.gender = random.choice(["male", "female"])
        self.safe_spot = []
        self.animals_nearby = []
        self.nearby_unoccupied_tiles = []
        self.nearby_occupied_tiles = []
        self.max_age = 365 * 10
        self.max_energy = 100
        self.birth_turn = 1
        self.emoji = "🐶"
        self.max_hunger = 100
        self.max_thirst = 100

    def check_nearby_tiles(self, grid):
        self.nearby_unoccupied_tiles = []
        self.animals_nearby = []
        self.nearby_occupied_tiles = []
        self.safe_spot = []

        for row, col in itertools.product(range(-1, self.speed), range(-1, self.speed)):
            # check if the grid position exists
            if 0 <= self.position[0] + row < len(grid) and 0 <= self.position[
                1
            ] + col < len(grid[0]):
                # check if the grid position is occupied
                if grid[self.position[0] + row][self.position[1] + col] is None:
                    self.nearby_unoccupied_tiles.append(
                        [self.position[0] + row, self.position[1] + col]
                    )
                elif isinstance(
                    grid[self.position[0] + row][self.position[1] + col], Animal
                ):
                    self.animals_nearby.append(
                        grid[self.position[0] + row][self.position[1] + col]
                    )
                else:
                    self.nearby_occupied_tiles.append(
                        grid[self.position[0] + row][self.position[1] + col]
                    )

        for tile in self.nearby_unoccupied_tiles:
            is_safe = not any(
                (0 <= tile[0] + row < len(grid) and 0 <= tile[1] + col < len(grid[0]))
                and (
                    grid[tile[0] + row][tile[1] + col] is not None
                    and isinstance(grid[tile[0] + row][tile[1] + col], Animal)
                )
                for row, col in itertools.product(range(-1, 2), range(-1, 2))
            )
            if is_safe:
                self.safe_spot.append(tile)

    def drink(self, water, zoo):
        """
        This method is called when the animal drinks.
        When an animal drinks the thirst attribute is increased by 1.
        If the water is empty, the thirst attribute is decreased by 1.
        An animal can die if its thirst attribute is 0.
        """
        if water.size > 1:
            water.size -= 1
            self.thirst += 1
            self.energy += 1
        else:
            self.thirst -= 1
            self.energy -= 1
            zoo.remove_water(water)

    def sleep(self, grid):
        """
        This method is called when the animal sleeps.
        """
        self.check_nearby_tiles(grid)
        quality_of_sleep = sum(1 for _ in self.nearby_unoccupied_tiles)
        for _ in self.nearby_occupied_tiles:
            quality_of_sleep -= 1
        for _ in self.animals_nearby:
            quality_of_sleep -= 1
        for _ in self.safe_spot:
            quality_of_sleep += 1
        self.sleep_counter = quality_of_sleep // 2
        self.energy += quality_of_sleep

    def mate(self, partner, grid):
        """
        This method is called when the animal mates.
        """

        if partner.virility > 0 and self.age > 1 and partner.age > 1:
            self.virility -= 1
            self.energy += 1
            for tile in self.nearby_unoccupied_tiles:
                row, col = tile
                if grid[row][col] is None:
                    baby = self.__class__()
                    baby.position = [row, col]
                    grid[row][col] = baby
                    return baby
        # return None if no baby was born
        return None

    def grow(self):
        """
        This method is called when the animal grows.
        """

        self.strength += random.randint(0, 1)
        self.speed += random.randint(0, 1)
        self.size += random.randint(0, 1)
        self.energy += random.randint(0, 1)
        self.virility += random.randint(0, 1)
        self.age += 1

    def die(self, zoo, reason):
        """
        This method is called when the animal dies.
        """
        logging.error(f"{self} died at {self.position} of {reason}.")
        self.strength = 0
        self.speed = 0
        self.size = 0
        self.hunger = 0
        self.thirst = 0
        self.energy = 0
        self.virility = 0
        self.is_alive = False
        # remove the animal from the grid
        zoo.grid[self.position[0]][self.position[1]] = None
        # remove the animal from the zoo
        with contextlib.suppress(ValueError):
            zoo.animals.remove(self)
        # replace the animal with a corpse if the position is not occupied
        if zoo.grid[self.position[0]][self.position[1]] is None:
            corpse = Corpse(self)
            zoo.grid[self.position[0]][self.position[1]] = corpse

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

    def move(self, direction, zoo):
        """
        This method is called when the animal moves. The direction is a list of two numbers.
        """
        # Only move if the new position is within the grid and occupied by None, grass, or dirt
        moved = False
        reason_not_to_move = None
        current_occupant = None
        try:
            current_occupant = zoo.grid[direction.position[0]][direction.position[1]]
        except TypeError:
            import pdb

            pdb.set_trace()
            pass
        except IndexError:
            import pdb

            pdb.set_trace()
            pass
        except AttributeError:
            current_occupant = zoo.grid[direction[0]][direction[1]]
        if current_occupant:
            occupant_is_bigger = (
                current_occupant.size > self.size if current_occupant else False
            )
            occupant_is_animal = isinstance(current_occupant, Animal)
            if occupant_is_animal:
                reason_not_to_move = f"Cannot move to {direction} because it is occupied by {current_occupant.__str__()}"
            elif occupant_is_bigger:
                reason_not_to_move = f"The {current_occupant.__str__()} is too big to move over."

        if current_occupant is None or isinstance(current_occupant, Grass) or not reason_not_to_move:
            if current_occupant:
                new_row = self.position[0] + current_occupant.position[0]
                new_col = self.position[1] + current_occupant.position[1]
            else:
                new_row = direction[0]
                new_col = direction[1]
            if 0 <= new_row < len(zoo.grid) and 0 <= new_col < len(zoo.grid[0]):
                # new position is within the grid, so update the position
                zoo.grid[self.position[0]][self.position[1]] = None
                self.position[0] = new_row
                self.position[1] = new_col
                zoo.grid[new_row][new_col] = self
                moved = True

        if moved:
            self.energy -= 1
            self.hunger -= 1
            self.thirst -= 1
            zoo.tiles_to_refresh.append(current_occupant)
            logging.error(f"{self.__class__.__name__} moved to {self.position}.")
        elif reason_not_to_move:
            logging.error(reason_not_to_move)

    def motivation(self, turn_number, zoo):
        """
        Determines the animal's most urgent need (drink, eat, sleep, or mate).
        """
        if not self.liveness_check():
            self.die(zoo, "natural causes")
            raise LifeException(f"{self.__class__.__name__} died of natural causes.")

        if self.sleep_counter > 0:
            self.sleep_counter -= 1
            self.motive = "sleep"
            return

        self.age = turn_number - self.birth_turn

        needs = {
            "drink": self.thirst,
            "eat": self.hunger,
            "sleep": self.energy,
            "mate": self.virility,
        }

        # Filter out any needs that are already being satisfied (i.e., attribute values of 0)
        unsatisfied_needs = {k: v for k, v in needs.items() if v > 0}

        # If all needs are being satisfied, choose a need at random
        if not unsatisfied_needs:
            self.motive = random.choice(list(needs.keys()))
        else:
            # Choose the need with the lowest value
            self.motive = min(unsatisfied_needs, key=unsatisfied_needs.get)

    def liveness_check(self):
        """
        Determines if the animal is still alive.
        """
        self.is_alive = (
            self.age <= self.max_age
            and self.hunger > 0
            and self.thirst > 0
            and self.energy > 0
        )
        return self.is_alive

    def turn(self, grid, zoo, turn_number):
        """
        This method is called when the animal takes a turn.
        """

        self.safe_spot = self.look_for_safe_spot(grid)
        self.motivation(turn_number, zoo)
        self.base_hunger(grid, zoo)
        self.base_thirst(grid, zoo)
        self.base_rest()
        if not zoo.full:
            self.base_reproduce(grid, zoo, turn_number)
        return self.motive

    def base_reproduce(self, grid, zoo, turn_number):
        if partner := self.check_for_mating_partner(grid):
            if baby := self.reproduce(partner, zoo, turn_number):
                zoo.animals.append(baby)

        else:
            # move towards random direction
            self.move([random.randint(-1, 1), random.randint(-1, 1)], zoo)

    def check_for_mating_partner(self, grid):
        # check for adjacent animals of the opposite sex
        for i, j in itertools.product(range(-1, 2), range(-1, 2)):
            row = self.position[0] + i
            col = self.position[1] + j
            if i == 0 and j == 0:
                continue
            if (
                0 <= row < len(grid)
                and 0 <= col < len(grid[0])
                and isinstance(grid[row][col], Animal)
                and grid[row][col].__str__() == self.__str__()
                and grid[row][col].gender != self.gender
                and grid[row][col].motive == "mate"
            ):
                return grid[row][col]
        return None

    def reproduce(self, partner, zoo, turn_number):
        # check if both animals have enough energy to reproduce
        zoo.check_full()
        self.check_nearby_tiles(zoo.grid)
        if zoo.full:
            return None
        if (
            self.energy < self.max_energy * 0.8
            or partner.energy < partner.max_energy * 0.8
        ):
            return None
        # create baby
        if self.nearby_unoccupied_tiles:
            baby_position = random.choice(self.nearby_unoccupied_tiles)
        else:
            return None
        baby = self.__class__()
        baby.size = int((self.size + partner.size) / 2)

        baby.strength = int((self.strength + partner.strength) / 2)
        baby.speed = int((self.speed + partner.speed) / 2)
        baby.virility = int((self.virility + partner.virility) / 2)
        baby.energy = int(self.max_energy * 0.4 + partner.max_energy * 0.4)
        baby.hunger = int(baby.max_hunger * 0.5)
        baby.thirst = int(baby.max_thirst * 0.5)
        baby.position = baby_position
        zoo.grid[baby_position[0]][baby_position[1]] = baby
        baby.birth_turn = turn_number
        baby.age = 0
        return baby

    def base_rest(self):
        if self.motive == "sleep":
            if not self.is_at_safe_spot():
                if safe_spot := self.look_for_safe_spot(self.zoo.grid):
                    self.move(safe_spot)
            if self.energy >= self.max_energy // 2:
                self.sleep()

    def is_at_safe_spot(self):
        return self.position == self.safe_spot

    def base_thirst(self, grid, zoo):
        if self.motive == "drink":
            if found_water := self.look_for_water(grid):
                self.move(found_water.position, zoo)
                self.drink(found_water, zoo)
            else:
                # move towards random direction
                direction = [random.randint(-1, 1), random.randint(-1, 1)]
                new_pos = [
                    self.position[0] + direction[0],
                    self.position[1] + direction[1],
                ]
                if 0 <= new_pos[0] < len(grid) and 0 <= new_pos[1] < len(grid[0]):
                    self.move(direction, zoo)

    def base_hunger(self, grid, zoo, func=None):
        if func is None:
            func = self.look_for_food
        if self.motive == "eat":
            if found_food := func(grid):
                self.move(found_food, zoo)
                self.eat(found_food, zoo)
            else:
                # move towards random direction
                self.move([random.randint(-1, 1), random.randint(-1, 1)], zoo)

    def look_for_food(self, grid, limit=None):
        """
        This method is called when the animal looks for food in the reach of the animal's speed.
        """
        food = []
        for i, j in itertools.product(
            range(-self.speed, self.speed + 1),
            range(-self.speed, self.speed + 1),
        ):
            if limit is not None and len(food) >= limit:
                break
            try:
                if grid[self.position[0] + i][self.position[1] + j] and isinstance(
                    grid[self.position[0] + i][self.position[1] + j], self.favorite_food
                ):
                    food.append(grid[self.position[0] + i][self.position[1] + j])
            except (TypeError, IndexError):
                continue
        return min(food, key=lambda x: x.size) if food else None

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
        min_index = self.speed
        max_index_i = len(grid) - self.speed
        max_index_j = len(grid[0]) - self.speed

        i_min = max(self.position[0] - self.speed, 0)
        i_max = min(self.position[0] + self.speed + 1, max_index_i)
        j_min = max(self.position[1] - self.speed, 0)
        j_max = min(self.position[1] + self.speed + 1, max_index_j)

        if nearby_water := [
            grid[i][j]
            for i, j in itertools.product(range(i_min, i_max), range(j_min, j_max))
            if isinstance(grid[i][j], Water)
        ]:
            return min(nearby_water, key=lambda x: x.size)
        return None

    def look_for_safe_spot(self, grid):
        """
        This method is called when the animal looks for a safe spot to mate or sleep.
        A safe spot is a spot where no other animal of the same species is present.
        """
        if self.safe_spot:
            return self.safe_spot

        # account for the edges of the grid
        if self.position[0] - self.speed < 0:
            self.position[0] = self.speed
        if self.position[0] + self.speed > len(grid) - 1:
            self.position[0] = len(grid) - 1 - self.speed
        if self.position[1] - self.speed < 0:
            self.position[1] = self.speed
        if self.position[1] + self.speed > len(grid[0]) - 1:
            self.position[1] = len(grid[0]) - 1 - self.speed

        try:
            nearby_safe_spots = [
                grid[self.position[0] + i][self.position[1] + j]
                for i, j in itertools.product(
                    range(-self.speed, self.speed + 1),
                    range(-self.speed, self.speed + 1),
                )
                if isinstance(
                    grid[self.position[0] + i][self.position[1] + j], self.__class__
                )
            ]
        except (TypeError, IndexError):
            nearby_safe_spots = []

        if empty_safe_spots := [
            spot for spot in nearby_safe_spots if not isinstance(spot, Animal)
        ]:
            return min(empty_safe_spots, key=lambda x: x.size)

        return None

    def eat(self, found_food, zoo):
        """
        If an Animal is adjacent to a compatible food it will eat it.
        When an Animal eats the nutrient value of the food is added to the Animal's hunger.
        An Animal can only eat one food per turn.
        An Animal could die if its hunger is 0 or below.
        """
        # compatible foods are either plants or animals or both. We can derive that by seeing the
        # base class of the favorite food.
        compatible_food_classes = (
            [self.favorite_food]
            if issubclass(self.favorite_food, Animal)
            else [Plant, Corpse]
        )
        has_eaten = False
        while not has_eaten:
            for compatible_food_class in compatible_food_classes:
                if isinstance(found_food, (Plant, Corpse)):
                    self.hunger += found_food.nutrition
                    zoo.grid[found_food.position[0]][found_food.position[1]] = None
                    found_food.die(zoo)
                    self.grow()
                    has_eaten = True
                    break
                elif isinstance(
                    grid[self.position[0] + i][self.position[1] + j],
                    Animal,
                ):
                    attack = self.attack(compatible_food_class)
                    defense = compatible_food_class.defend(opponent=self)
                    if attack > defense:
                        compatible_food_class.energy -= attack - defense
                        if compatible_food_class.energy <= 0:
                            # the food is dead now, replace it with a dead animal
                            compatible_food_class.die(zoo)
        # if the animal has not eaten it will grow even more hungry
        if not has_eaten:
            self.hunger += 1


class Carnivore(Animal):
    """
    This is the class for carnivores.
    """

    def __init__(self):
        """
        This method is called when the carnivore is created.
        """
        super().__init__()
        self.favorite_food = Animal

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
        super().__init__()
        self.favorite_food = Plant

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
        super().__init__()
        self.favorite_food = random.choice([Plant, Animal])

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
        super().__init__()
        self.favorite_food = Prey

    def __str__(self):
        """
        This method is called when the predator is printed.
        """

        return "Predator"

    def turn(self, grid, zoo, turn_number):
        """
        This method is called when the animal takes a turn.
        """
        self.motivation(turn_number, zoo)
        self.predator_hunger(grid, zoo)
        self.base_thirst(grid, zoo)
        self.base_rest()
        zoo.check_full()
        if not zoo.full:
            self.base_reproduce(grid, zoo, turn_number)
        self.age = turn_number - self.birth_turn
        return self.motive

    def predator_hunger(self, grid, zoo):
        if self.motive == "hunger":
            if found_food := self.hunt(grid):
                self.move(found_food)
                self.eat(found_food, zoo)

    def hunt(self, grid):
        """
        This method is called when the predator hunts.
        The predator will check the surrounding tiles for prey and move towards it.
        The predator can move its speed in any direction and will attack the prey if it is in range.
        """
        self.check_nearby_tiles(grid)

        for animal in self.animals_nearby:
            if not isinstance(animal, Predator):
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
        super().__init__()
        self.favorite_food = Plant

    def __str__(self):
        """
        This method is called when the prey is printed.
        """

        return "Prey"

    def run_away(self, grid):
        """
        If the prey is near a predator, it will run away.
        """
        self.check_nearby_tiles(grid)

        try:
            nearest_predator = min(
                self.animals_nearby, key=lambda x: abs(x.position[0] - self.position[0])
            )
        except ValueError:
            nearest_predator = None
        if nearest_predator and isinstance(nearest_predator, Predator):
            # the prey will change its position to an unoccupied tile adjacent to the predator
            self.check_nearby_tiles(grid)
            with contextlib.suppress(IndexError):
                self.position = random.choice(self.nearby_unoccupied_tiles)

    def turn(self, grid, zoo, turn_number):
        """
        This method is called when the animal takes a turn.
        """
        self.run_away(grid)
        self.motivation(turn_number, zoo)
        self.base_hunger(grid, zoo)
        self.base_thirst(grid, zoo)
        self.base_rest()
        zoo.check_full()
        if not zoo.full:
            self.base_reproduce(grid, zoo, turn_number)
        self.age = turn_number - self.birth_turn
        return self.motive


class Scavenger(Animal):
    """
    This is the class for scavengers.
    """

    def __init__(self):
        """
        This method is called when the scavenger is created.
        """
        super().__init__()
        self.favorite_food = Corpse

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
        if self.nearby_occupied_tiles:
            nearest_dead_animal = min(
                self.nearby_occupied_tiles,
                key=lambda x: abs(x.position[0] - self.position[0]),
            )
        else:
            nearest_dead_animal = None
        if nearest_dead_animal and isinstance(nearest_dead_animal, Corpse):
            # the scavenger will change its position to an unoccupied tile adjacent to the dead animal
            self.check_nearby_tiles(grid)
            self.position = random.choice(self.nearby_unoccupied_tiles)

    def turn(self, grid, zoo, turn_number):
        """
        This method is called when the animal takes a turn.
        """
        self.motivation(turn_number, zoo)
        self.base_hunger(grid, zoo, func=self.scavenge)
        self.base_thirst(grid, zoo)
        self.base_rest()
        zoo.check_full()
        if not zoo.full:
            self.base_reproduce(grid, zoo, turn_number)
        self.age = turn_number - self.birth_turn
        return self.motive


class Lion(Predator):
    """
    This is the class for lions.
    """

    def __init__(self):
        """
        This method is called when the lion is created.
        """
        super().__init__()
        self.strength = 5
        self.size = 5
        self.favorite_food = Zebra
        self.emoji = "🦁"
        self.max_age = 10 * 365

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
        super().__init__()
        self.favorite_food = Grass
        self.speed = 5
        self.size = 3
        self.emoji = "🦓"
        self.max_age = 10 * 365

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
        super().__init__()
        self.strength = 10
        self.size = 10
        self.favorite_food = Tree
        self.emoji = "🐘"
        self.max_age = 30 * 365

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
        super().__init__()
        self.strength = 3
        self.size = 3
        self.favorite_food = Corpse
        self.emoji = "🦡"
        self.max_age = 10 * 365

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
        super().__init__()
        self.favorite_food = Tree
        self.speed = 3
        self.size = 5
        self.emoji = "🦒"
        self.max_age = 10 * 365

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
        super().__init__()
        self.strength = 7
        self.size = 7
        self.favorite_food = Bush
        self.emoji = "🦏"
        self.max_age = 10 * 365

    def __str__(self):
        """
        This method is called when the rhino is printed.
        """

        return "Rhino"
