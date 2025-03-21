import textwrap

def pretty_print_error(error_message):
    try:
        # Convert escape sequences (like \n and \t) to their actual characters.
        unescaped_message = error_message.encode('utf-8').decode('unicode_escape')
    except Exception:
        unescaped_message = error_message

    # Wrap each line to 100 characters for readability.
    wrapped_lines = [textwrap.fill(line, width=100) for line in unescaped_message.splitlines()]
    return "\n".join(wrapped_lines)
 