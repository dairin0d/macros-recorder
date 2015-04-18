Macros Recorder
===============

Click on `Record Macro` to start recording; click `Recording... (Stop)` to stop recording. The recorded
commands would be written to a new text block when the recording is stopped.
Note that starting the recording from a 3D View would allow you to record some extra context information,
such as pivot mode and transform orientation.

`Please keep in mind:`
The script does not guarantee to record the correct history of operations if there were undos/redos during
the recording. For example, in Edit Mode, if you undo an operation, it won't get erased from the record.
Also, the results may be not reproducible because of the wrong context, or due to the differences between
operators' behavior in modal and non-modal regimes.

The addon also allows you to save parameters of procedurally generated objects and regenerate them
afterwards. To save procedural parameters, invoke "Regenerate procedural object" operator just after you
have created the object. Invoke it again anytime afterwards to change the parameters.

`Important!`
Procedural parameters are saved in the active object, so make sure the right one is selected.
Also, regeneration would replace the whole object's data, so any changes you did to mesh/curve/etc.
would be erased.

Installing
----------

Hit `Ctrl+Alt+U` to load up the User Preferences (or use the `File` menu and click `Save User Settings`).
Click the `Install Addon...` button at the bottom, then navigate to the `development_macros_recorder.py` script.

Check the little box on the right of the Addon entry in the list to enable it.
If, for some reason, you have a hard time finding it, you can search for `Macros Recorder`, or click on the
`Development` button on the left.

If you want to keep this addon available at all times, follow the above steps on a fresh `.blend`
(`Ctrl+N` to create one), then hit `Ctrl+U` at this point. The next time you run Blender, you won't have
to repeat the above.

When enabled, it would add `Record Macro` menu entry to the Text menu in the Text Editor, and a panel in
the Tool Shelf with the button to record/stop recording.

Contact information
-------------------

Upload Tracker:
http://projects.blender.org/tracker/index.php?func=detail&aid=31325