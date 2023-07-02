from collections import defaultdict

file_in = open("drawio.xml")
tag = "TAG"
adjective = "taggy"
noun = "Tag"

def find_value(string, start_string, end_string):
    start_index = string.find(start_string) + len(start_string)
    end_index = string.find(end_string, start_index)
    return string[start_index:end_index]

def find_indexes(start_string, end_string):
    element_id = find_value(line, start_string, end_string)
    find_string = "id = " + cell_dict[element_id]

    nf_id_index = -1
    for nf_line in nf_contents_list:
        nf_id_index += 1

        if find_string in nf_line:
            break
    
    nf_start_index = nf_id_index-1
    nf_end_index = nf_id_index

    while nf_end_index < len(nf_contents_list):
        nf_end_index += 1

        if nf_contents_list[nf_end_index] == "\t}\n":
            break

    return nf_start_index, nf_end_index+1

def get_scope(lines_list, start_string, end_string):
    string_indexes = find_indexes(start_string, end_string)
    return lines_list[string_indexes[0]:string_indexes[1]]

contents_list = file_in.readlines()

y_anchor = 40
x_anchor = 40
x_spacing = 80
y_spacing = 80
fetch_geometry = False

break_line_check = False
empty = True
cell_dict = {}

# check if file is empty at all
for line in contents_list:
    if '" value="' in line:
        focus_name = find_value(line, '" value="', '" style="')

        for char in ["&#39;", "&lt;span&gt;", "&lt;/span&gt;"]: # this is reused somewhere else
            if char in focus_name:
                focus_name = focus_name.replace(char, "")

        if focus_name != "": # contains a focus; good to go
            empty = False
            break

if not empty:
    # write an empty focus file
    file_out = open("common\\national_focus\\" + noun + ".txt", "w")
    file_out.write("focus_tree = {\n\tid = " + adjective + "_focus\n\n\tcountry = {\n\t\tfactor = 0\n\n\t\tmodifier = {\n\t\t\tadd = 10\n\t\t\ttag = GER\n\t\t}\n\t}\n\n")
    file_out.close()

    # write an empty loc file
    with open("localisation\\test_l_english.yml", "w", encoding="utf-8-sig") as loc_out:
        loc_out.write("l_english:")
        loc_out.close()

    focus_true_pos_dict = {}
    for line in contents_list:
        if '" value="' in line and '" value=""' not in line: # if value exists and not empty
            fetch_geometry = True # delayed instruction for the next line
            focus_name = find_value(line, '" value="', '" style="')

            for char in ["&#39;", "&lt;span&gt;", "&lt;/span&gt;"]:
                if char in focus_name:
                    focus_name = focus_name.replace(char, "")
            
            if focus_name != "":
                focus_id = focus_name
                focus_id = focus_id.lower()

                focus_id = focus_id.replace(" ", "_")
                focus_id = focus_id.replace("-", "_")

                for char in "\"'!,":
                    if char in focus_id:
                        focus_id = focus_id.replace(char, "")

                focus_id = tag + "_" + focus_id

                with open("localisation\\test_l_english.yml", "a") as loc_out:
                    loc_out.write("\n " + focus_id +":0 " + '"'+focus_name+'"')

                cell_id = find_value(line, '<mxCell id="', '" value="')
                cell_dict[cell_id] = focus_id

        elif fetch_geometry:
            fetch_geometry = False # reset

            x_pos = int(round(float(find_value(line, 'x="', '" y="')), -1))
            y_pos = int(round(float(find_value(line, '" y="', '" width="')), -1))

            x_pos -= x_anchor
            x_pos = x_pos // x_spacing

            y_pos -= y_anchor
            y_pos = y_pos // y_spacing

            focus_true_pos_dict[focus_id] = [x_pos, y_pos]
            
            # write basic focus
            with open("common\\national_focus\\" + noun + ".txt", "a") as file_out:
                file_out.write("\tfocus = {\n\t\tid = " + focus_id + "\n\t\ticon = GFX_goal_unknown\n\t\tx = " + str(x_pos) + " y = " + str(y_pos) + "\n\t\tcost = 10\n\t\tcompletion_reward = {}\n\t}\n\n")

    # close focuses
    with open("common\\national_focus\\" + noun + ".txt", "a") as file_out:
        file_out.write("}")

    # arrow check
    for line in contents_list:
        if "source=" in line and "target=" in line: # if this line describes an arrow
            nf_file = open("common\\national_focus\\" + noun + ".txt")
            nf_contents_list = nf_file.readlines()

            target_strings = ['" target="', '"']
            source_strings = ['" source="', '" target="']
            target_element_id = find_value(line, target_strings[0], target_strings[1])
            source_element_id = find_value(line, source_strings[0], source_strings[1])

            target_y = focus_true_pos_dict[cell_dict[target_element_id]][1]
            source_y = focus_true_pos_dict[cell_dict[source_element_id]][1]
            
            if target_y > source_y:
                higher_id = cell_dict[source_element_id]
                nf_indexes = find_indexes(target_strings[0], target_strings[1])
            elif source_y > target_y:
                higher_id = cell_dict[target_element_id]
                nf_indexes = find_indexes(source_strings[0], source_strings[1])

            nf_index_id = nf_indexes[0]
            nf_index_end = nf_indexes[1]
            current_scope = nf_contents_list[nf_index_id:nf_index_end]

            if ";dashed=1;" in line:
                if "\t\tprerequisite = { #\n" in current_scope:
                    dashed_index = current_scope.index("\t\tprerequisite = { #\n")
                    current_scope.insert(dashed_index+1, "\t\t\tfocus = " + higher_id + "\n")

                    nf_contents_list[nf_index_id:nf_index_end] = current_scope

                else:
                    nf_contents_list[nf_index_id+2:nf_index_id+2] = ["\t\tprerequisite = { #\n", "\t\t}\n"]
                    nf_contents_list.insert(nf_index_id+3, "\t\t\tfocus = " + higher_id + "\n")

            else:
                nf_contents_list[nf_index_id+2:nf_index_id+2] = ["\t\tprerequisite = {\n", "\t\t}\n"]
                nf_contents_list.insert(nf_index_id+3, "\t\t\tfocus = " + higher_id + "\n")

            nf_contents = "".join(nf_contents_list)
            nf_file = open("common\\national_focus\\" + noun + ".txt", "w")
            nf_file.write(nf_contents)
            nf_file.close()
    
    # sort by y position
    nf_file = open("common\\national_focus\\" + noun + ".txt")
    nf_contents = nf_file.read()
    nf_focus_list = nf_contents.split("\n\n")

    focus_y_dict = defaultdict(list)
    nf_focus_id = -1
    focus_y_max = 0
    nf_focus_list_trim = nf_focus_list[3:-1]
    for focus in nf_focus_list_trim:
        nf_focus_id += 1

        focus_y = int(find_value(focus, " y = ", "\n"))
        if focus_y not in focus_y_dict:
            focus_y_dict[focus_y] = [focus]
        else:
            focus_y_dict[focus_y].append(focus)
        
        if focus_y > focus_y_max:
            focus_y_max = focus_y

    content_focus_list = []
    for y_pos in range(focus_y_max):
        for focus in focus_y_dict[y_pos]:
            content_focus_list.append(focus)

    nf_focus_list[3:-1] = content_focus_list

    nf_contents = "\n\n".join(nf_focus_list)
    nf_file = open("common\\national_focus\\" + noun + ".txt", "w")
    nf_file.write(nf_contents)
    nf_file.close()

    # set position by prerequisite    
    nf_file = open("common\\national_focus\\" + noun + ".txt")
    nf_contents = nf_file.read()
    nf_focus_list = nf_contents.split("\n\n")
    nf_focus_list_trim = nf_focus_list[3:-1]

    nf_focus_list_index =-1
    for focus in nf_focus_list_trim:
        nf_focus_list_index += 1
        focus_lines = focus.split("\n")
        if "\t\tprerequisite = { #" not in focus_lines:
            prereq_count = focus_lines.count("\t\tprerequisite = {")
            if prereq_count == 1:
                prereq_index = focus_lines.index("\t\tprerequisite = {")
                focus_line = focus_lines[prereq_index+1] + "\n"
                focus_id_prereq = find_value(focus_line, "\t\t\tfocus = ", "\n")

                focus_id_current = find_value(focus_lines[1]+"\n", "\t\tid = ", "\n")
                for focus in nf_focus_list_trim:
                    if "\t\tid = "+focus_id_prereq in focus:
                        x_relative = focus_true_pos_dict[focus_id_current][0] - focus_true_pos_dict[focus_id_prereq][0]
                        y_relative = focus_true_pos_dict[focus_id_current][1] - focus_true_pos_dict[focus_id_prereq][1]
                        break
                
                focus_line_index = -1
                for line in focus_lines:
                    focus_line_index += 1
                    if "\t\tx = " in line and " y = " in line:
                        break
                
                focus_lines[focus_line_index] = "\t\trelative_position_id = " + focus_id_prereq + "\n\t\tx = " + str(x_relative) + " y = " + str(y_relative)
                nf_focus_list_trim[nf_focus_list_index] = "\n".join(focus_lines)
    
    nf_focus_list[3:-1] = nf_focus_list_trim
    nf_contents = "\n\n".join(nf_focus_list)
    nf_file = open("common\\national_focus\\" + noun + ".txt", "w")
    nf_file.write(nf_contents)
    nf_file.close()

    # generate auxiliary stuff
    with open("localisation\\test_l_english.yml", 'rb') as open_file:
        content = open_file.read()
    content = content.replace(b'\r\n', b'\n')
    with open("localisation\\test_l_english.yml", 'wb') as open_file:
        open_file.write(content)
