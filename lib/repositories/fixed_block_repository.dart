import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/fixed_block.dart';

class FixedBlockRepository {
  final SupabaseClient _client = Supabase.instance.client;

  Future<List<FixedBlock>> getFixedBlocks(String userId) async {
    final response = await _client
        .from('fixed_blocks')
        .select()
        .eq('user_id', userId);
    return response.map((e) => FixedBlock.fromMap(e)).toList();
  }

  Future<List<FixedBlock>> getFixedBlocksByDay(String userId, String dayOfWeek) async {
    final response = await _client
        .from('fixed_blocks')
        .select()
        .eq('user_id', userId)
        .eq('day_of_week', dayOfWeek);
    return response.map((e) => FixedBlock.fromMap(e)).toList();
  }

  Future<FixedBlock> createFixedBlock(
    String userId,
    String title,
    String type,
    String dayOfWeek,
    String startTime,
    String endTime,
  ) async {
    final response = await _client.from('fixed_blocks').insert({
      'user_id': userId,
      'title': title,
      'type': type,
      'day_of_week': dayOfWeek,
      'start_time': startTime,
      'end_time': endTime,
    }).select().single();
    return FixedBlock.fromMap(response);
  }

  Future<void> updateFixedBlock(
    String blockId,
    String title,
    String type,
    String dayOfWeek,
    String startTime,
    String endTime,
  ) async {
    await _client.from('fixed_blocks').update({
      'title': title,
      'type': type,
      'day_of_week': dayOfWeek,
      'start_time': startTime,
      'end_time': endTime,
    }).eq('id', blockId);
  }

  Future<void> deleteFixedBlock(String blockId) async {
    await _client.from('fixed_blocks').delete().eq('id', blockId);
  }
}