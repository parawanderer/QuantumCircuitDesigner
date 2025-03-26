import math

from base.models import CircuitDefinition
from ui.constants import DiagramConstants


def determine_placement_spot(x0: float,
                             y0: float,
                             x1: float,
                             y1: float,
                             lines_offset_x: float,
                             lines_offset_y: float,
                             schedule: CircuitDefinition,
                             allow_multi_pairs_of: int = None) -> tuple[int, int] | None:
    """
    Will determine the best placement for a gate contained within the position (`x0`, `y0`, `x1`, `y1`)
    The idea goes something like this:

    For any such object, it has a mid point of (xp, yp).
    The object has (at most) 4 surrounding possible points, 
    that can be interpreted as NW, NE, SW, SE. They are equally 
    spaced in regards to each other.

    ```
                                 
          NW                NE   
            o              o     
                                 
                                 
                                 
                                 
                      ● Obj      
                                 
                                 
                                 
            o              o     
          SW                SE   
                                 
    ```
    
    xp and yp are floating point numbers (decimal)
    the x and y coordinates of the possible positions are integers

    The points of these positions are as follows for some x and y:
    
    ```
    SW = (x, y)
    SE = (x + 1, y)
    NW = (x, y + 1)
    NE = (x + 1, y + 1)
    ```

    the object, which we'll call `Obj`, has mid-point coordinates of: (xp, yp)
    Where:
    ```
    xp = in range x, x+1(inclusive)
    yp = in range y, y+1(inclusive)
    ```

    The target position will be the best position in relation to the surrounding points 
    (so long as that position is actually available: not already occupied by another gate).

    So basically we can use the pythagoras theorem to get the distances of `Obj`
    to each point, and of these distances we choose the point with the min distance 
    as the target.

    If this target is not available at that point, we'll return that there's no target at all.

    The rest of the logic is concerned with special cases of allowing to steal spots or what area we want to consider.
    
    """

    x = ((x0 + x1) / 2) - lines_offset_x - DiagramConstants.BLOCK_SIZE
    y = ((y0 + y1) / 2) - lines_offset_y

    x_block = x / DiagramConstants.BLOCK_DOUBLE
    y_block = y / DiagramConstants.BLOCK_DOUBLE

    if y_block > schedule.num_qubits - 0.5: # offset from the "schedule"/"circuit" is too large
        return None

    # find NE, NW, SE, SW 
    # the set is needed because if we drop an object at exact integer 
    # coordinates then the rounding will not lead to different positions,
    # it will lead to duplicates. The set filters the duplicates for us
    available_spots: set[tuple[int, int]] = set()
    available_spots.add((math.floor(x_block), math.floor(y_block)))
    available_spots.add((math.floor(x_block), math.ceil(y_block)))
    available_spots.add((math.ceil(x_block), math.floor(y_block)))
    available_spots.add((math.ceil(x_block), math.ceil(y_block)))

    min_distance = float("inf")
    target_time = None
    target_qubit = None
    # determine closest
    for (time, qubit) in available_spots:
        if time < 0 or qubit < 0 or qubit >= schedule.num_qubits:
            # invalid positions
            continue
        
        # the actual distance does not matter to us, 
        # just which one is closer, 
        # so we can skip the square root here
        x = time - x_block
        y = qubit - y_block
        distance = x*x + y*y

        if distance < min_distance:
            min_distance = distance
            target_time = time
            target_qubit = qubit

    if target_time is None:
        return None

    if schedule.is_nop(target_qubit, target_time):
        return target_qubit, target_time

    if (allow_multi_pairs_of is not None and
            (schedule.is_multi_target_pair(allow_multi_pairs_of, target_qubit, target_time))):
        return target_qubit, target_time

    return None
