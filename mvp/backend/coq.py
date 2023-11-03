import subprocess

# Start coqtop as a subprocess with piping enabled for communication
process = subprocess.Popen(['coqtop'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

def send_command(cmd):
    process.stdin.write(cmd + "\n")
    process.stdin.flush()
    # Reading the output; you might need more sophisticated handling for larger outputs.
    out = process.stdout.readline()
    while "Coq <" not in out or "my_first_lemma <" not in out:
        print(out, end="")
        out = process.stdout.readline()
    print(out, end="")  # Print the prompt

    return out


if  __name__ == "__main__":
    # Define the lemma
    send_command("Lemma my_first_lemma : forall n: nat, n + 0 = n.")

    # Start the proof
    send_command("Proof.")

    # # Provide the proof tactics
    send_command("intros n.")
    # send_command("simpl.")
    # send_command("reflexivity.")
    # send_command("Qed.")
