import os

project = 'data/CompCert'
files = {}
files['flocq/Calc/Fcalc_round.v'] = ['inbetween_int_NE']
files['flocq/Core/Fcalc_Zaux.v'] = ['Zopp_le_cancel', 'Zgt_not_eq', 'radix_gt_0', 'Zsame_sign_imp', 'cond_Zopp_negb', 'abs_cond_Zopp', 'cond_Zopp_Zlt_bool', 'iter_nat_S']
files['common/Globalenvs.v'] = ['shift_symbol_address', 'shift_symbol_address_32', 'shift_symbol_address_64', 'find_funct', 'find_funct_ptr', 'find_funct_ptr_iff', 'find_var_info_iff', 'global_addresses_distinct', 'genv_next_add_globals', 'genv_public_add_globals', 'alloc_globals_app']
files['lib/Parmov.v'] = ['update_same', 'update_o', 'update_ident', 'dests_disjoint_sym', 'dests_disjoint_cons_right', 'is_mill_cons', 'move_no_temp_append', 'notin_dests_cons', 'exec_seq_app', 'env_equiv_sym', 'env_equiv_trans', 'parmove2_wf_moves', 'no_overlap_sym', 'pairwise_disjoint_norepet', 'disjoint_temps_not_temp', 'mu_is_mill', 'no_overlap_pairwise', 'weak_exec_seq_match']
files['x86/SelectOpproof.v'] = ['eval_addrstack', 'eval_mulhs', 'eval_mulhu', 'eval_negf', 'eval_absf', 'eval_negfs', 'eval_absfs', 'eval_compf', 'eval_compfs', 'eval_singleoffloat', 'eval_floatofsingle', 'eval_intoffloat', 'eval_intofsingle']
files['backend/Locations.v'] = ['typesize_pos', 'typealign_pos', 'typealign_typesize', 'same_not_diff', 'Loc.diff_sym', 'Loc.disjoint_cons_left', 'IndexedTyp.index_inj', 'IndexedSlot.index_inj', 'OrderedLoc.eq_sym', 'OrderedLoc.eq_trans', 'OrderedLoc.lt_trans']
files['cfrontend/Cop.v'] = ['ArithConv.typeconv_integer_promotion']

proved_theorems = ['eval_addrstack', 'eval_mulhs', 'eval_mulhu', 'eval_negf', 'eval_absf', 'eval_negfs', 'eval_absfs', 'eval_compf', 'eval_compfs', 'eval_singleoffloat', 'eval_floatofsingle', 'eval_intoffloat', 'eval_intofsingle', 'typesize_pos', 'typealign_pos', 'typealign_typesize', 'same_not_diff', 'Loc.diff_sym', 'Loc.disjoint_cons_left', 'IndexedTyp.index_inj', 'IndexedSlot.index_inj', 'OrderedLoc.eq_sym', 'OrderedLoc.eq_trans', 'OrderedLoc.lt_trans', 'ArithConv.typeconv_integer_promotion', 'typesize_pos', 'typealign_pos', 'typealign_typesize', 'same_not_diff', 'Loc.diff_sym', 'Loc.disjoint_cons_left', 'IndexedTyp.index_inj', 'IndexedSlot.index_inj', 'OrderedLoc.eq_sym', 'OrderedLoc.eq_trans', 'OrderedLoc.lt_trans', 'ArithConv.typeconv_integer_promotion']

# Create a list of json paths to theorems
paths_and_theorems = {}
for coq_path, theorems in files.items():
    for theorem in theorems:
        if theorem in proved_theorems:
            json_path = os.path.join(project, coq_path.replace(".v", ".json"))
            paths_and_theorems[json_path] = paths_and_theorems.get(json_path, []) + [theorem]

# print(paths_and_theorems)

counter = 0
for _, values in files.items():
    counter += len(values)
print(counter)



# Below are the theorems that were successfully proved by proverbot
    # - path: x86/SelectOpproof.v
    #   theorems:
    #     - eval_addrstack
    #     - eval_mulhs
    #     - eval_mulhu
    #     - eval_negf
    #     - eval_absf
    #     - eval_negfs
    #     - eval_absfs
    #     - eval_compf
    #     - eval_compfs
    #     - eval_singleoffloat
    #     - eval_floatofsingle
    #     - eval_intoffloat
    #     - eval_intofsingle
    #   - path: backend/Locations.v
    #     theorems:
    #       - typesize_pos
    #       - typealign_pos
    #       - typealign_typesize
    #       - same_not_diff
    #       - Loc.diff_sym
    #       - Loc.disjoint_cons_left
    #       - IndexedTyp.index_inj
    #       - IndexedSlot.index_inj
    #       - OrderedLoc.eq_sym
    #       - OrderedLoc.eq_trans
    #       - OrderedLoc.lt_trans
    #   - path: cfrontend/Cop.v
    #     theorems: 
    #       - ArithConv.typeconv_integer_promotion

