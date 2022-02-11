import freezegun

# Exclude the current module from time freezes.
freezegun.configure(extend_ignore_list=[__package__])
