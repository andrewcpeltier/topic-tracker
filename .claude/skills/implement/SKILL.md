---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

If the user passes a ticket reference, fetch it from the issue tracker and state its title before starting. If the reference is ambiguous, ask.

Call the Skill tool with "tdd" where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Then call the Skill tool with "verify-change": it decides from the ticket whether the Click-through runs, and gives the `Click-through:` line for the PR.

Once done, call the Skill tool with "code-review" to review the work, including any spec the Click-through added. If the review changes code on the path that spec walks, run the Click-through again.

Commit your work to the current branch.
