def is_sunny(cloud_cover_dict):
    """Return True if all time blocks are ≤ 20% cloud cover."""
    try:
        values = [int(v.strip('%')) for v in cloud_cover_dict.values()]
        return all(v <= 20 for v in values)
    except Exception:
        return False
    
def compare_cloud_cover(predicted, actual, tolerance=10):
    """
    Compare predicted vs actual cloud cover.
    Returns number of matching time blocks (out of 3).
    """
    matches = 0
    for time in ["morning", "afternoon", "evening"]:
        try:
            pred_val = int(predicted[time].strip('%'))
            actual_val = int(actual[time].strip('%'))
            if abs(pred_val - actual_val) <= tolerance:
                matches += 1
        except Exception:
            continue
    return matches